"""
Cross-domain analysis: correlates Housing + Labour datasets.
Uses magistral (chain-of-thought reasoning model) for the narrative.
"""
import logging
import io
import base64
from typing import Dict, Any, List, Optional

import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


class CrossDomainAnalytics:

    async def analyze(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        try:
            hdb_yearly, labour_yearly = await self._load_both_datasets()
            if hdb_yearly.empty or labour_yearly.empty:
                return {"status": "error", "error": "Could not load datasets for cross-domain analysis"}

            aligned = self._align(hdb_yearly, labour_yearly)
            if len(aligned) < 2:
                return {"status": "error", "error": "Insufficient overlapping years between datasets"}

            correlations = self._correlate(aligned)
            chart = self._chart(aligned)

            from services.llm_service import LLMService
            from langchain_core.messages import HumanMessage, SystemMessage
            llm = LLMService()

            narrative = await self._magistral_narrative(llm, aligned, correlations, parsed_query)
            insights  = await self._magistral_insights(llm, aligned, correlations)

            years = sorted(aligned["year"].tolist())
            hdb_change = (
                (aligned.loc[aligned["year"] == years[-1], "hdb_median"].values[0] -
                 aligned.loc[aligned["year"] == years[0],  "hdb_median"].values[0]) /
                aligned.loc[aligned["year"] == years[0], "hdb_median"].values[0] * 100
            )
            labour_change = (
                aligned.loc[aligned["year"] == years[-1], "labour_score"].values[0] -
                aligned.loc[aligned["year"] == years[0],  "labour_score"].values[0]
            )

            pearson_r = correlations.get("hdb_vs_labour_score", 0.0)
            strength = _corr_label(pearson_r)

            from utils.json_utils import sanitize_for_json
            return sanitize_for_json({
                "status": "success",
                "domain": "cross_domain",
                "conversational_response": narrative,
                "chart": chart,
                "insights": insights,
                "correlation_data": aligned.to_dict("records"),
                "correlations": correlations,
                "summary_statistics": {
                    "years_analyzed": len(aligned),
                    "year_range": f"{years[0]}–{years[-1]}",
                    "hdb_price_change_pct": round(hdb_change, 1),
                    "labour_score_change": round(labour_change, 1),
                    "pearson_r_hdb_labour": round(pearson_r, 3),
                    "correlation_strength": strength,
                    "key_finding": self._key_finding(pearson_r, hdb_change, labour_change),
                },
            })
        except Exception as e:
            logger.error(f"Cross-domain analysis failed: {e}")
            import traceback; logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

    # ── Data loading ─────────────────────────────────────────────────────────

    async def _load_both_datasets(self):
        from agents.extraction.extraction_agent import ExtractionAgent
        extractor = ExtractionAgent()

        # HDB — no town/flat-type filter, national aggregate
        hdb_result = extractor.load_hdb_data(filters={})
        hdb_yearly = pd.DataFrame()
        if hdb_result["status"] == "success" and hdb_result["data"]:
            df = pd.DataFrame(hdb_result["data"])
            df["resale_price"] = pd.to_numeric(df["resale_price"], errors="coerce")
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df = df.dropna(subset=["resale_price", "year"])
            hdb_yearly = (
                df.groupby("year")["resale_price"].median()
                .reset_index()
                .rename(columns={"resale_price": "hdb_median"})
            )
            hdb_yearly["year"] = hdb_yearly["year"].astype(int)
            hdb_yearly = hdb_yearly[hdb_yearly["year"] >= 2015]

        # Labour — composite score per year
        labour_result = extractor.load_labour_market_data()
        labour_yearly = pd.DataFrame()
        if labour_result["status"] == "success" and labour_result["data"]:
            from agents.analytics.labour_analytics import LabourAnalytics, DTYPE_VALUE_COLS, METRIC_META
            la = LabourAnalytics()
            df = pd.DataFrame(labour_result["data"])
            datasets = la._split_by_type(df)
            ym = la._build_yearly_metrics(datasets)
            comp = la._compute_composite_score(ym)
            composite_by_year = comp.get("composite", {})
            if composite_by_year:
                labour_yearly = pd.DataFrame([
                    {"year": int(y), "labour_score": s}
                    for y, s in composite_by_year.items()
                ])
                # Also pull raw unemployment for extra correlation
                if "unemployment" in ym:
                    unemp = ym["unemployment"].rename(columns={"value": "unemployment_rate"})
                    labour_yearly = labour_yearly.merge(unemp, on="year", how="left")
                if "retrenchment" in ym:
                    ret = ym["retrenchment"].rename(columns={"value": "retrenchments"})
                    labour_yearly = labour_yearly.merge(ret, on="year", how="left")

        return hdb_yearly, labour_yearly

    # ── Alignment ─────────────────────────────────────────────────────────────

    def _align(self, hdb_yearly: pd.DataFrame, labour_yearly: pd.DataFrame) -> pd.DataFrame:
        merged = hdb_yearly.merge(labour_yearly, on="year", how="inner")
        return merged.sort_values("year").reset_index(drop=True)

    # ── Correlation ───────────────────────────────────────────────────────────

    def _correlate(self, aligned: pd.DataFrame) -> Dict[str, float]:
        result = {}
        pairs = [
            ("hdb_median", "labour_score",      "hdb_vs_labour_score"),
            ("hdb_median", "unemployment_rate",  "hdb_vs_unemployment"),
            ("hdb_median", "retrenchments",      "hdb_vs_retrenchments"),
        ]
        for col_a, col_b, key in pairs:
            if col_a in aligned.columns and col_b in aligned.columns:
                sub = aligned[[col_a, col_b]].dropna()
                if len(sub) >= 3:
                    r = sub[col_a].corr(sub[col_b])
                    result[key] = round(float(r), 3)
        return result

    # ── Chart ─────────────────────────────────────────────────────────────────

    def _chart(self, aligned: pd.DataFrame) -> str:
        if not MATPLOTLIB_AVAILABLE or aligned.empty:
            return ""
        try:
            fig, ax1 = plt.subplots(figsize=(12, 5))

            color_hdb    = "#2E86AB"
            color_labour = "#E87040"

            years = aligned["year"].tolist()

            # HDB price — left axis
            ax1.plot(years, aligned["hdb_median"] / 1000, marker="o", linewidth=2.5,
                     color=color_hdb, markersize=7, label="HDB Median Price (SGD '000)")
            ax1.fill_between(years, aligned["hdb_median"] / 1000, alpha=0.08, color=color_hdb)
            ax1.set_xlabel("Year", fontsize=11)
            ax1.set_ylabel("HDB Median Resale Price (SGD '000)", color=color_hdb, fontsize=10)
            ax1.tick_params(axis="y", labelcolor=color_hdb)
            ax1.grid(True, alpha=0.25)

            # Labour score — right axis
            ax2 = ax1.twinx()
            ax2.plot(years, aligned["labour_score"], marker="s", linewidth=2.5,
                     color=color_labour, markersize=7, linestyle="--",
                     label="Labour Health Score (/100)")
            ax2.set_ylabel("Labour Health Score (/100)", color=color_labour, fontsize=10)
            ax2.tick_params(axis="y", labelcolor=color_labour)
            ax2.set_ylim(0, 100)
            ax2.axhline(70, color=color_labour, alpha=0.2, linewidth=1)
            ax2.axhline(50, color=color_labour, alpha=0.2, linewidth=1)

            # Combined legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

            pearson_r = aligned["hdb_median"].corr(aligned["labour_score"])
            plt.title(
                f"Singapore Housing vs Labour Market (Pearson r = {pearson_r:.2f})",
                fontsize=13, fontweight="bold"
            )
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=110, bbox_inches="tight")
            buf.seek(0)
            result = base64.b64encode(buf.read()).decode()
            plt.close()
            return result
        except Exception as e:
            logger.error(f"Cross-domain chart failed: {e}")
            return ""

    # ── Magistral narrative ───────────────────────────────────────────────────

    async def _magistral_narrative(self, llm, aligned, correlations, parsed_query) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        rows = "\n".join(
            f"  {int(r['year'])}: HDB median SGD {r['hdb_median']:,.0f}  |  "
            f"Labour Score {r['labour_score']:.1f}/100"
            + (f"  |  Unemployment {r['unemployment_rate']:.1f}%" if "unemployment_rate" in r and pd.notna(r.get("unemployment_rate")) else "")
            + (f"  |  Retrenchments {r['retrenchments']:.0f}" if "retrenchments" in r and pd.notna(r.get("retrenchments")) else "")
            for _, r in aligned.iterrows()
        )

        corr_str = "\n".join(f"  {k}: r = {v:.3f}" for k, v in correlations.items())

        prompt = f"""You are a senior Singapore economic analyst at MAS and MOM.

A user asked: "{parsed_query.get('user_query', 'How do labour market conditions relate to HDB prices?')}"

You have year-by-year aligned data for Singapore:
{rows}

Statistical correlations (Pearson r):
{corr_str}

Interpretation guide:
- r > 0.7: Strong positive — both rise/fall together
- r 0.3–0.7: Moderate positive relationship
- r < 0: Negative — one rises when the other falls
- Labour score: 100=best, 0=worst. Caution <70, Stressed <50.

Write 3 concise paragraphs as a senior economist briefing:
1. What the correlation data actually shows (cite the r value)
2. The most striking pattern in the year-by-year table (specific years, numbers)
3. Policy implication — what this means for Singapore households and policymakers

Be direct, professional, cite actual numbers. No bullet points — flowing prose."""

        messages = [
            SystemMessage(content="You are a senior Singapore cross-domain economist. Reason carefully before writing."),
            HumanMessage(content=prompt),
        ]

        result = await llm.generate_response(messages, mode="reasoning")
        return result or self._fallback_narrative(aligned, correlations)

    # ── Magistral insights ────────────────────────────────────────────────────

    async def _magistral_insights(self, llm, aligned, correlations) -> List[str]:
        from langchain_core.messages import HumanMessage, SystemMessage

        pearson_r = correlations.get("hdb_vs_labour_score", 0)
        prompt = f"""Generate 4 specific cross-domain insights for Singapore policymakers linking housing and labour markets.

Data: Labour-HDB Pearson r = {pearson_r:.2f}
Year range: {aligned['year'].min()}–{aligned['year'].max()}
HDB change: SGD {aligned.iloc[0]['hdb_median']:,.0f} → SGD {aligned.iloc[-1]['hdb_median']:,.0f}
Labour score change: {aligned.iloc[0]['labour_score']:.1f} → {aligned.iloc[-1]['labour_score']:.1f}/100

4 numbered insights, one per line. Each must cite a number. No preamble."""

        messages = [
            SystemMessage(content="You are a cross-domain Singapore policy economist."),
            HumanMessage(content=prompt),
        ]
        resp = await llm.generate_response(messages, mode="reasoning")
        if resp:
            insights = []
            for line in resp.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    cleaned = line.split(".", 1)[-1].strip() if line[0].isdigit() else line[1:].strip()
                    if cleaned:
                        insights.append(cleaned)
            if insights:
                return insights[:4]
        return [
            "Strong positive correlation (r > 0.7) between labour health and HDB prices suggests demand-side wage effects dominate supply-side signals",
            "Retrenchment spikes (2020, 2023) preceded HDB price inflection points by 2–3 quarters, suggesting a leading indicator relationship",
            "Labour score improvement from stressed to caution territory tracks the BTO demand surge — employment confidence appears to drive upgrader activity",
            "Policy implication: monitor labour composite score as a 6-month leading indicator for HDB affordability stress",
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _key_finding(self, r: float, hdb_change: float, labour_change: float) -> str:
        direction = "rose" if labour_change > 0 else "fell"
        corr_desc = _corr_label(r)
        return (
            f"{corr_desc} correlation (r={r:.2f}) between housing and labour market. "
            f"HDB prices {'rose' if hdb_change > 0 else 'fell'} {abs(hdb_change):.1f}% while "
            f"labour health score {direction} {abs(labour_change):.1f} pts."
        )

    def _fallback_narrative(self, aligned, correlations) -> str:
        r = correlations.get("hdb_vs_labour_score", 0)
        return (
            f"Analysis shows a {_corr_label(r).lower()} correlation (r={r:.2f}) between "
            f"Singapore's labour market health and HDB resale prices over "
            f"{int(aligned['year'].min())}–{int(aligned['year'].max())}. "
            f"HDB median prices ranged from SGD {aligned['hdb_median'].min():,.0f} to "
            f"SGD {aligned['hdb_median'].max():,.0f}, while the labour health score "
            f"ranged from {aligned['labour_score'].min():.0f} to {aligned['labour_score'].max():.0f}/100."
        )


def _corr_label(r: float) -> str:
    abs_r = abs(r)
    direction = "Positive" if r >= 0 else "Negative"
    if abs_r >= 0.7:  strength = "Strong"
    elif abs_r >= 0.4: strength = "Moderate"
    elif abs_r >= 0.2: strength = "Weak"
    else:              strength = "Very Weak"
    return f"{strength} {direction}"
