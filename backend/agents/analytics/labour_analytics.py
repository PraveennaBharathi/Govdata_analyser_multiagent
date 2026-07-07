import pandas as pd
import io
import base64
import logging
from typing import Dict, Any, List, Optional

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

# How each metric maps to "health" — which direction is good
DTYPE_VALUE_COLS = {
    "unemployment":           "seasonally_adj_unemp_rate",
    "retrenchment":           "retrench",
    "recruitment":            "recruitment_rate",
    "long_term_unemployment": "ltu_rate",
}

METRIC_META = {
    # anchor_low / anchor_high are absolute reference bounds so scores aren't
    # relative to the observed window (which made 2020 score 0 in COVID years).
    "unemployment":          {"label": "Unemployment Rate",       "unit": "%",  "lower_is_better": True,  "weight": 0.30, "anchor_low": 0.5,  "anchor_high": 8.0},
    "retrenchment":          {"label": "Quarterly Retrenchments", "unit": "",   "lower_is_better": True,  "weight": 0.25, "anchor_low": 500,  "anchor_high": 15000},
    "recruitment":           {"label": "Recruitment Rate",        "unit": "%",  "lower_is_better": False, "weight": 0.25, "anchor_low": 0.5,  "anchor_high": 4.0},
    "long_term_unemployment":{"label": "Long-term Unemployment",  "unit": "%",  "lower_is_better": True,  "weight": 0.20, "anchor_low": 0.1,  "anchor_high": 2.0},
}

EXCLUDE_COLS = {"dataset_type", "year", "period", "quarter", "_period",
                "residential_status", "res_stat", "type"}


class LabourAnalytics:
    """Multi-dataset Singapore labour market analysis with composite health score."""

    async def analyze(self, data: List[Dict], parsed_query: Dict, forced_model: str = None) -> Dict[str, Any]:
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return {"status": "error", "error": "No labour data available"}

            datasets = self._split_by_type(df)
            if not datasets:
                return {"status": "error", "error": "Could not parse labour datasets"}

            yearly_metrics = self._build_yearly_metrics(datasets)
            composite = self._compute_composite_score(yearly_metrics)
            chart = self._chart(yearly_metrics, composite)

            latest_year = int(max(ym["year"].max() for ym in yearly_metrics.values() if not ym.empty))
            per_metric_scores = composite.get("per_metric", {})
            composite_by_year = composite.get("composite", {})

            from services.llm_service import LLMService
            from langchain_core.messages import HumanMessage, SystemMessage
            llm = LLMService()

            summary_rows = []
            for dtype, ym in yearly_metrics.items():
                if not ym.empty and "value" in ym.columns:
                    meta = METRIC_META.get(dtype, {})
                    latest_val = ym[ym["year"] == ym["year"].max()]["value"].mean()
                    earliest_val = ym[ym["year"] == ym["year"].min()]["value"].mean()
                    change = latest_val - earliest_val
                    summary_rows.append(
                        f"- {meta.get('label', dtype)}: {latest_val:.2f}{meta.get('unit','')} "
                        f"(change since {int(ym['year'].min())}: {change:+.2f}{meta.get('unit','')})"
                    )

            composite_latest = composite.get("composite", {})
            score_now = composite_latest.get(latest_year, 50) if isinstance(composite_latest, dict) else 50

            score_now = composite_by_year.get(latest_year, 50.0)
            metric_scores_now = {
                dtype: scores.get(latest_year, 0.0)
                for dtype, scores in per_metric_scores.items()
            }

            prompt = f"""You are a Singapore labour market analyst briefing the Ministry of Manpower.
Write 2-3 conversational paragraphs summarising Singapore's current labour market health.

Labour Health Score (composite, 0-100, 100=best): {score_now:.0f}/100
Status: {'Healthy' if score_now >= 70 else 'Caution' if score_now >= 50 else 'Stressed'}

Current metrics (latest available data):
{chr(10).join(summary_rows)}

Write in a direct, professional tone. Lead with the composite assessment, then discuss the most significant trend, then give context.
Use actual numbers from the data above. Do not use bullet points — flowing paragraphs only."""

            messages = [
                SystemMessage(content="You are a senior Singapore labour market economist."),
                HumanMessage(content=prompt),
            ]
            conversational = await llm.generate_response(messages, mode="narrative", forced_model=forced_model) or self._fallback_narrative(score_now, summary_rows, yearly_metrics)

            insights = await self._insights(llm, yearly_metrics, composite, forced_model=forced_model)

            from utils.json_utils import sanitize_for_json
            result = {
                "status": "success",
                "domain": "labour",
                "conversational_response": conversational,
                "yearly_metrics": {k: v.to_dict("records") for k, v in yearly_metrics.items() if not v.empty},
                "composite_score": composite,
                "insights": insights,
                "chart": chart,
                "summary_statistics": {
                    "labour_health_score": round(score_now, 1),
                    "health_status": "Healthy" if score_now >= 70 else "Caution" if score_now >= 50 else "Stressed",
                    "latest_year": latest_year,
                    "datasets_analysed": list(datasets.keys()),
                    "metric_scores": {k: round(v, 1) for k, v in metric_scores_now.items()},
                },
            }
            return sanitize_for_json(result)

        except Exception as e:
            logger.error(f"Labour analysis failed: {e}")
            import traceback; logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------ #

    def _split_by_type(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        result = {}
        for dtype in df["dataset_type"].unique():
            sub = df[df["dataset_type"] == dtype].copy()
            if "year" not in sub.columns:
                continue
            sub["year"] = pd.to_numeric(sub["year"], errors="coerce")
            sub = sub.dropna(subset=["year"])
            sub["year"] = sub["year"].astype(int)
            result[dtype] = sub
        return result

    def _build_yearly_metrics(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        result = {}
        for dtype, df in datasets.items():
            vcol = DTYPE_VALUE_COLS.get(dtype)
            if vcol is None or vcol not in df.columns:
                continue
            df = df.copy()
            df[vcol] = pd.to_numeric(df[vcol], errors="coerce")
            # Drop rows where the value is NaN (happens when merged schema fills with NaN)
            df = df.dropna(subset=[vcol])
            if df.empty:
                continue
            ym = df.groupby("year")[vcol].mean().reset_index()
            ym.columns = ["year", "value"]
            ym = ym[ym["year"] >= 2015].sort_values("year")
            ym = ym.dropna(subset=["value"])
            if not ym.empty:
                result[dtype] = ym
        return result

    def _compute_composite_score(self, yearly_metrics: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Normalise each metric to 0–100 and compute a weighted composite.
        Returns per-type yearly scores + composite yearly scores.
        """
        all_years = sorted(set(
            y for ym in yearly_metrics.values() for y in ym["year"].tolist()
        ))
        scores_by_type: Dict[str, Dict[int, float]] = {}
        composite_by_year: Dict[int, float] = {y: 0.0 for y in all_years}
        total_weight_by_year: Dict[int, float] = {y: 0.0 for y in all_years}

        for dtype, ym in yearly_metrics.items():
            if ym.empty:
                continue
            meta = METRIC_META.get(dtype, {"lower_is_better": True, "weight": 0.25, "anchor_low": None, "anchor_high": None})
            # Use absolute anchors when provided so the score isn't relative to
            # the observed window (which made COVID years score 0 or 100).
            a_low = meta.get("anchor_low")
            a_high = meta.get("anchor_high")
            if a_low is not None and a_high is not None:
                vmin, vmax = a_low, a_high
            else:
                vmin, vmax = ym["value"].min(), ym["value"].max()
            rng = vmax - vmin if vmax != vmin else 1.0

            dtype_scores: Dict[int, float] = {}
            for _, row in ym.iterrows():
                year = int(row["year"])
                raw = row["value"]
                norm = max(0.0, min(1.0, (raw - vmin) / rng))  # clamp to [0,1]
                score = (1 - norm) * 100 if meta["lower_is_better"] else norm * 100
                dtype_scores[year] = score

            scores_by_type[dtype] = dtype_scores
            weight = meta["weight"]
            for year, score in dtype_scores.items():
                composite_by_year[year] += score * weight
                total_weight_by_year[year] += weight

        # Normalise composite by actual weights present each year
        composite_normalised = {}
        for year in all_years:
            tw = total_weight_by_year.get(year, 0)
            composite_normalised[year] = composite_by_year[year] / tw if tw > 0 else 50.0

        return {
            "per_metric": {k: {int(yr): round(s, 1) for yr, s in v.items()}
                           for k, v in scores_by_type.items()},
            "composite": {int(y): round(s, 1) for y, s in composite_normalised.items()},
        }

    def _chart(self, yearly_metrics: Dict[str, pd.DataFrame], composite: Dict) -> str:
        if not MATPLOTLIB_AVAILABLE or not yearly_metrics:
            return ""
        try:
            n = len(yearly_metrics)
            cols = 2
            rows = (n + 1) // cols + 1  # +1 row for composite
            fig, axes = plt.subplots(rows, cols, figsize=(14, rows * 3.5))
            axes = axes.flatten()

            colors = ["#2E86AB", "#E87040", "#44BBA4", "#F18F01"]
            for idx, (dtype, ym) in enumerate(yearly_metrics.items()):
                if ym.empty:
                    continue
                ax = axes[idx]
                meta = METRIC_META.get(dtype, {"label": dtype, "unit": ""})
                color = colors[idx % len(colors)]
                ax.plot(ym["year"], ym["value"], marker="o", linewidth=2,
                        color=color, markersize=6)
                ax.fill_between(ym["year"], ym["value"], alpha=0.12, color=color)
                ax.set_title(meta["label"], fontsize=11, fontweight="bold")
                ax.set_ylabel(meta.get("unit", ""))
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis="x", rotation=45)

            # Composite score panel
            comp_data = composite.get("composite", {})
            if comp_data:
                ax = axes[n]
                years = sorted(comp_data.keys())
                scores = [comp_data[y] for y in years]
                bar_colors = ["#27AE60" if s >= 70 else "#F39C12" if s >= 50 else "#E74C3C"
                              for s in scores]
                ax.bar(years, scores, color=bar_colors, alpha=0.85)
                ax.axhline(70, color="#27AE60", linestyle="--", alpha=0.5, linewidth=1, label="Healthy (70)")
                ax.axhline(50, color="#F39C12", linestyle="--", alpha=0.5, linewidth=1, label="Caution (50)")
                ax.set_title("Labour Health Score (Composite)", fontsize=11, fontweight="bold")
                ax.set_ylabel("Score / 100")
                ax.set_ylim(0, 100)
                ax.legend(fontsize=8)
                ax.grid(True, alpha=0.3, axis="y")
                ax.tick_params(axis="x", rotation=45)

            # Hide unused axes
            for i in range(n + 1, len(axes)):
                axes[i].set_visible(False)

            plt.suptitle("Singapore Labour Market Dashboard", fontsize=13, fontweight="bold", y=1.01)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            result = base64.b64encode(buf.read()).decode()
            plt.close()
            return result
        except Exception as e:
            logger.error(f"Labour chart failed: {e}")
            return ""

    async def _insights(self, llm, yearly_metrics, composite, forced_model=None) -> List[str]:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            comp = composite.get("composite", {})
            years = sorted(comp.keys())
            if len(years) >= 3:
                baseline = comp[years[-3]]
            elif len(years) == 2:
                baseline = comp[years[0]]
            else:
                baseline = comp[years[-1]]
            trend = "improving" if comp[years[-1]] > baseline else "deteriorating"

            prompt = f"""Generate 4 specific, numbered policy insights for MOM about Singapore's labour market.
Composite score trend: {trend} (latest: {comp.get(years[-1], 50):.0f}/100)
Metric scores latest year: {composite.get('per_metric', {})}
One insight per line. Be specific with implications. No bullet points — numbered list only."""
            messages = [
                SystemMessage(content="You are a senior MOM labour economist."),
                HumanMessage(content=prompt),
            ]
            resp = await llm.generate_response(messages, mode="narrative", forced_model=forced_model)
            if resp:
                insights = []
                for line in resp.split("\n"):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        cleaned = line.split(".", 1)[-1].strip() if line[0].isdigit() else line[1:].strip()
                        if cleaned:
                            insights.append(cleaned)
                return insights[:5]
        except Exception:
            pass
        return [
            "Monitor retrenchment-to-recruitment ratio as a leading indicator of market slack",
            "Long-term unemployment elevation signals structural mismatch requiring reskilling intervention",
            "Recruitment rate strength suggests demand-side resilience despite supply-side pressure",
            "Composite score trajectory should inform timing of any workforce support programmes",
        ]

    def _fallback_narrative(self, score: float, summary_rows: List[str], yearly_metrics: dict = None) -> str:
        status = "**healthy**" if score >= 70 else "**cautionary**" if score >= 50 else "**stressed**"

        parts = [
            f"Singapore's labour market is currently in a {status} state with a composite health "
            f"score of **{score:.0f}/100** (0 = stressed, 100 = healthy). "
            f"This composite is derived from four live MOM indicators: unemployment rate, quarterly "
            f"retrenchments, recruitment rate, and long-term unemployment."
        ]

        if summary_rows:
            parts.append("**Current indicator values:**\n" + "\n".join(summary_rows))

        # Year-specific highlights from actual data
        if yearly_metrics:
            highlights = []
            unemp = yearly_metrics.get("unemployment")
            rtrench = yearly_metrics.get("retrenchment")
            recruit = yearly_metrics.get("recruitment")

            if unemp is not None and not unemp.empty:
                latest_u = unemp.loc[unemp["year"].idxmax()]
                peak_u   = unemp.loc[unemp["value"].idxmax()]
                highlights.append(
                    f"Unemployment rate: **{latest_u['value']:.2f}%** (latest {int(latest_u['year'])}); "
                    f"peaked at **{peak_u['value']:.2f}%** in {int(peak_u['year'])}."
                )

            if rtrench is not None and not rtrench.empty:
                worst_r = rtrench.loc[rtrench["value"].idxmax()]
                latest_r = rtrench.loc[rtrench["year"].idxmax()]
                highlights.append(
                    f"Retrenchments: highest in **{int(worst_r['year'])}** at ~{int(worst_r['value']):,}/quarter; "
                    f"latest ({int(latest_r['year'])}): ~{int(latest_r['value']):,}/quarter."
                )

            if recruit is not None and not recruit.empty:
                latest_rec = recruit.loc[recruit["year"].idxmax()]
                highlights.append(
                    f"Recruitment rate: **{latest_rec['value']:.2f}%** in {int(latest_rec['year'])}."
                )

            if highlights:
                parts.append("**Key data points:**\n" + "\n".join(highlights))

        if score >= 70:
            parts.append("Overall, the market reflects sustained demand and structural resilience.")
        elif score >= 50:
            parts.append("Some indicators warrant continued monitoring — particularly retrenchment volumes and long-term unemployment trends.")
        else:
            parts.append("The stressed score signals significant headwinds requiring targeted workforce support and reskilling programmes.")

        return "\n\n".join(parts)
