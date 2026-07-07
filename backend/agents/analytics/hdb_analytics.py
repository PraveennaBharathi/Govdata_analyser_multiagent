import pandas as pd
import io
import base64
import logging
from typing import Dict, Any, List

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

# Sub-areas / estates that are NOT standalone HDB towns → map to their parent town
# (The 26 HDB towns in data.gov.sg resale data don't include sub-estate names)
_SUBZONE_TO_TOWN: Dict[str, str] = {
    "BOON LAY":        "JURONG WEST",
    "BOONLAY":         "JURONG WEST",
    "LAKESIDE":        "JURONG WEST",
    "CHINESE GARDEN":  "JURONG WEST",
    "PIONEER":         "JURONG WEST",
    "PAYA LEBAR":      "GEYLANG",
    "ALJUNIED":        "GEYLANG",
    "KEMBANGAN":       "BEDOK",
    "TANAH MERAH":     "BEDOK",
    "CHAI CHEE":       "BEDOK",
    "EUNOS":           "GEYLANG",
    "MACPHERSON":      "GEYLANG",
    "BRADDELL":        "TOA PAYOH",
    "KIM KEAT":        "TOA PAYOH",
    "LORONG 8 TOA PAYOH": "TOA PAYOH",
    "SIMEI":           "TAMPINES",
    "LOYANG":          "PASIR RIS",
    "COMPASSVALE":     "SENGKANG",
    "RIVERVALE":       "SENGKANG",
    "ANCHORVALE":      "SENGKANG",
    "FERNVALE":        "SENGKANG",
    "BUANGKOK":        "HOUGANG",
    "KOVAN":           "HOUGANG",
    "UPP SERANGOON":   "HOUGANG",
    "AMK":             "ANG MO KIO",
}


class HDBAnalytics:
    """Analytics for HDB resale flat price data."""

    async def analyze(self, data: List[Dict], parsed_query: Dict, forced_model: str = None) -> Dict[str, Any]:
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return {"status": "error", "error": "No HDB data"}

            df = self._prepare(df)

            town_filter = parsed_query.get("filters", {}).get("town")
            flat_filter = parsed_query.get("filters", {}).get("flat_type")

            if town_filter:
                t_upper = town_filter.upper().strip()
                # Step 1: exact match
                mask = df["town"].str.upper() == t_upper
                # Step 2: space-normalised match (handles "BOONLAY" → "BOON LAY")
                if not mask.any():
                    t_nospace = t_upper.replace(" ", "")
                    mask = df["town"].str.upper().str.replace(" ", "", regex=False) == t_nospace
                # Step 3: sub-area remapping (estates not classified as standalone HDB towns)
                if not mask.any():
                    remapped = _SUBZONE_TO_TOWN.get(t_upper)
                    if remapped:
                        logger.info(f"Remapping '{t_upper}' → '{remapped}' (sub-area of HDB town)")
                        mask = df["town"].str.upper() == remapped
                        town_filter = remapped
                if mask.any():
                    df = df[mask]
                    town_filter = df["town"].iloc[0]
                else:
                    logger.warning(f"Town filter '{town_filter}' not found in data — showing all towns")
                    town_filter = None
            if flat_filter:
                mask = df["flat_type"].str.upper() == flat_filter.upper()
                if mask.any():
                    df = df[mask]

            yearly = df.groupby("year")["resale_price"].agg(["median", "mean", "count"]).reset_index()
            yearly.columns = ["year", "median_price", "mean_price", "transactions"]

            town_summary = (
                df[df["year"] == df["year"].max()]
                .groupby("town")["resale_price"]
                .median()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"resale_price": "median_price"})
            )

            flat_summary = (
                df.groupby("flat_type")["resale_price"]
                .median()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"resale_price": "median_price"})
            )

            from services.llm_service import LLMService
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = LLMService()
            price_change_pct = (
                (yearly.iloc[-1]["median_price"] - yearly.iloc[0]["median_price"])
                / yearly.iloc[0]["median_price"] * 100
            ) if len(yearly) >= 2 else 0

            prompt = f"""You are a Singapore housing policy analyst.
Summarize this HDB resale data in 2-3 conversational paragraphs for a policy briefing.

Period: {int(yearly['year'].min())} to {int(yearly['year'].max())}
Transactions: {len(df):,}
Median price (start): SGD {int(yearly.iloc[0]['median_price']):,}
Median price (latest): SGD {int(yearly.iloc[-1]['median_price']):,}
Price change: {price_change_pct:.1f}%
Most expensive towns: {', '.join(town_summary['town'].head(3).tolist())}
Most affordable towns: {', '.join(town_summary['town'].tail(3).tolist())}
Top flat types by price: {', '.join(flat_summary['flat_type'].head(3).tolist())}
{'Town filter: ' + str(town_filter) if town_filter else ''}
{'Flat type filter: ' + str(flat_filter) if flat_filter else ''}

Write in a warm, professional tone. Give direct numbers, then context."""

            messages = [
                SystemMessage(content="You are a Singapore housing policy analyst."),
                HumanMessage(content=prompt),
            ]
            conversational = await llm.generate_response(messages, mode="narrative", forced_model=forced_model) or self._fallback_response(yearly, price_change_pct, town_filter, flat_filter, town_summary, flat_summary)

            insights = await self._insights(llm, yearly, town_summary, flat_summary, forced_model=forced_model)
            chart = self._chart(yearly, town_summary)
            storey_summary = self._storey_summary(df)
            psm_summary = self._psm_summary(df)
            town_momentum = self._town_momentum(df)

            from utils.json_utils import sanitize_for_json
            result = {
                "status": "success",
                "domain": "housing",
                "conversational_response": conversational,
                "yearly_trends": yearly.to_dict("records"),
                "town_summary": town_summary.head(10).to_dict("records"),
                "town_summary_bottom": town_summary.tail(5).to_dict("records"),
                "flat_type_summary": flat_summary.to_dict("records"),
                "storey_summary": storey_summary,
                "psm_summary": psm_summary,
                "town_momentum": town_momentum,
                "insights": insights,
                "chart": chart,
                "summary_statistics": {
                    "total_transactions": int(len(df)),
                    "years_covered": f"{int(yearly['year'].min())}-{int(yearly['year'].max())}",
                    "overall_median_price": int(df["resale_price"].median()),
                    "price_change_pct": round(price_change_pct, 1),
                    "most_expensive_town": town_summary.iloc[0]["town"] if not town_summary.empty else "N/A",
                    "most_affordable_town": town_summary.iloc[-1]["town"] if not town_summary.empty else "N/A",
                    "most_affordable_price": int(town_summary.iloc[-1]["median_price"]) if not town_summary.empty else 0,
                    "top_flat_type": flat_summary.iloc[0]["flat_type"] if not flat_summary.empty else "N/A",
                    "high_floor_premium_pct": self._high_floor_premium(storey_summary),
                },
            }
            return sanitize_for_json(result)

        except Exception as e:
            logger.error(f"HDB analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["resale_price"] = pd.to_numeric(df["resale_price"], errors="coerce")
        df["floor_area_sqm"] = pd.to_numeric(df["floor_area_sqm"], errors="coerce")
        df = df.dropna(subset=["resale_price", "month"])
        df["year"] = df["month"].str[:4].astype(int)
        df = df[df["year"] >= 2020]
        # Storey band — parse "07 TO 09" → extract lower floor number
        df["storey_low"] = df["storey_range"].str.extract(r"(\d+)").astype(float)
        df["storey_band"] = pd.cut(
            df["storey_low"],
            bins=[0, 6, 15, 100],
            labels=["Low (1–6)", "Mid (7–15)", "High (16+)"],
        )
        # Price per sqm
        df["price_per_sqm"] = df["resale_price"] / df["floor_area_sqm"].replace(0, float("nan"))
        return df

    def _storey_summary(self, df: pd.DataFrame) -> List[Dict]:
        try:
            s = (
                df.groupby("storey_band", observed=True)["resale_price"]
                .agg(["median", "count"])
                .reset_index()
                .rename(columns={"storey_band": "band", "median": "median_price", "count": "transactions"})
            )
            s["median_price"] = s["median_price"].round(0)
            return s.to_dict("records")
        except Exception:
            return []

    def _psm_summary(self, df: pd.DataFrame) -> List[Dict]:
        """Price per sqm by flat type — size-normalised comparison."""
        try:
            s = (
                df.dropna(subset=["price_per_sqm"])
                .groupby("flat_type")["price_per_sqm"]
                .median()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"price_per_sqm": "median_psm"})
            )
            s["median_psm"] = s["median_psm"].round(0)
            return s.to_dict("records")
        except Exception:
            return []

    def _town_momentum(self, df: pd.DataFrame) -> List[Dict]:
        """Which towns have accelerated the most recently (2023–2025 vs 2020–2022)."""
        try:
            early = df[df["year"].isin([2020, 2021, 2022])].groupby("town")["resale_price"].median()
            recent = df[df["year"].isin([2023, 2024, 2025])].groupby("town")["resale_price"].median()
            merged = pd.DataFrame({"early": early, "recent": recent}).dropna()
            merged["momentum_pct"] = ((merged["recent"] - merged["early"]) / merged["early"] * 100).round(1)
            merged = merged.sort_values("momentum_pct", ascending=False).reset_index()
            merged = merged.rename(columns={"early": "price_2020_22", "recent": "price_2023_25"})
            return merged.head(10).to_dict("records")
        except Exception:
            return []

    async def _insights(self, llm, yearly, town_summary, flat_summary, forced_model=None) -> List[str]:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            prompt = f"""Generate 4 concise policy insights for Singapore housing decision-makers:
Yearly price data: {yearly[['year','median_price','transactions']].to_dict('records')}
Top 5 towns by price: {town_summary.head(5).to_dict('records')}
Flat type prices: {flat_summary.to_dict('records')}
Return a numbered list, one insight per line."""
            messages = [
                SystemMessage(content="You are a Singapore housing policy analyst."),
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
            "HDB resale prices have shown significant appreciation since 2020",
            "Central and mature estates command premium prices",
            "Larger flat types (EA, MULTI-GEN) show the highest absolute prices",
            "Transaction volumes reflect sustained buyer demand despite cooling measures",
        ]

    def _chart(self, yearly: pd.DataFrame, town_summary: pd.DataFrame) -> str:
        if not MATPLOTLIB_AVAILABLE:
            return ""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            plt.style.use("seaborn-v0_8")

            ax1.plot(yearly["year"], yearly["median_price"] / 1000, marker="o",
                     linewidth=2, color="#E87040", markersize=8)
            ax1.fill_between(yearly["year"], yearly["median_price"] / 1000, alpha=0.15, color="#E87040")
            ax1.set_title("HDB Resale Median Price Trend", fontsize=14, fontweight="bold")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Median Resale Price (SGD '000)")
            ax1.grid(True, alpha=0.3)

            top10 = town_summary.head(10)
            colors = ["#C0392B" if i < 3 else "#2980B9" for i in range(len(top10))]
            ax2.barh(top10["town"][::-1], top10["median_price"][::-1] / 1000, color=colors[::-1])
            ax2.set_title(f"Median Price by Town ({int(yearly['year'].max())})", fontsize=14, fontweight="bold")
            ax2.set_xlabel("Median Resale Price (SGD '000)")
            ax2.grid(True, alpha=0.3, axis="x")

            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            result = base64.b64encode(buf.read()).decode()
            plt.close()
            return result
        except Exception as e:
            logger.error(f"HDB chart failed: {e}")
            return ""

    def _high_floor_premium(self, storey_summary: List[Dict]) -> float:
        try:
            bands = {r["band"]: r["median_price"] for r in storey_summary}
            low = bands.get("Low (1–6)", 0)
            high = bands.get("High (16+)", 0)
            if low > 0 and high > 0:
                return round((high - low) / low * 100, 1)
        except Exception:
            pass
        return 0.0

    def _fallback_response(self, yearly, price_change_pct, town_filter=None, flat_filter=None, town_summary=None, flat_summary=None) -> str:
        start_year  = int(yearly.iloc[0]["year"])
        end_year    = int(yearly.iloc[-1]["year"])
        start_price = int(yearly.iloc[0]["median_price"])
        latest      = int(yearly.iloc[-1]["median_price"])
        total_tx    = int(yearly["transactions"].sum())

        if town_filter and flat_filter:
            subject = f"{flat_filter.title()} flats in {town_filter.title()}"
        elif town_filter:
            subject = f"HDB resale flats in **{town_filter.title()}**"
        elif flat_filter:
            subject = f"**{flat_filter.title()}** HDB resale flats"
        else:
            subject = "the Singapore HDB resale market"

        parts = [
            f"From {start_year} to {end_year}, {subject} recorded **{total_tx:,} transactions**. "
            f"Median prices rose from **SGD {start_price:,}** to **SGD {latest:,}** — "
            f"a **{price_change_pct:.1f}% increase** over the period."
        ]

        # Year-by-year highlights
        if len(yearly) >= 2:
            peak = yearly.loc[yearly["median_price"].idxmax()]
            parts.append(
                f"Prices peaked at **SGD {int(peak['median_price']):,}** in {int(peak['year'])}, "
                f"with {int(peak['transactions']):,} transactions that year."
            )

        # Town breakdown (only when not already filtered to one town)
        if town_summary is not None and not town_summary.empty and not town_filter:
            top3    = town_summary.head(3)
            bottom3 = town_summary.tail(3)
            top_str = ", ".join(
                f"{r['town'].title()} (SGD {int(r['median_price']):,})"
                for _, r in top3.iterrows()
            )
            bot_str = ", ".join(
                f"{r['town'].title()} (SGD {int(r['median_price']):,})"
                for _, r in bottom3.iterrows()
            )
            parts.append(f"**Most expensive** towns in {end_year}: {top_str}.")
            parts.append(f"**Most affordable** towns in {end_year}: {bot_str}.")

        # Flat type breakdown (only when not filtered to one type)
        if flat_summary is not None and not flat_summary.empty and not flat_filter:
            top_flat = flat_summary.iloc[0]
            bot_flat = flat_summary.iloc[-1]
            parts.append(
                f"**{top_flat['flat_type'].title()}** flats command the highest median at "
                f"SGD {int(top_flat['median_price']):,}; "
                f"**{bot_flat['flat_type'].title()}** flats are the most affordable at "
                f"SGD {int(bot_flat['median_price']):,}."
            )

        return "\n\n".join(parts)
