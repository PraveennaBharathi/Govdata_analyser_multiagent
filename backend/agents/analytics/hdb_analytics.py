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


class HDBAnalytics:
    """Analytics for HDB resale flat price data."""

    async def analyze(self, data: List[Dict], parsed_query: Dict) -> Dict[str, Any]:
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return {"status": "error", "error": "No HDB data"}

            df = self._prepare(df)

            town_filter = parsed_query.get("filters", {}).get("town")
            flat_filter = parsed_query.get("filters", {}).get("flat_type")

            if town_filter:
                mask = df["town"].str.upper() == town_filter.upper()
                if mask.any():
                    df = df[mask]
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
            conversational = await llm.generate_response(messages, mode="narrative") or self._fallback_response(yearly, price_change_pct)

            insights = await self._insights(llm, yearly, town_summary, flat_summary)
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
            merged = merged.rename(columns={"town": "town", "early": "price_2020_22", "recent": "price_2023_25"})
            return merged.head(10).to_dict("records")
        except Exception:
            return []

    async def _insights(self, llm, yearly, town_summary, flat_summary) -> List[str]:
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
            resp = await llm.generate_response(messages, mode="narrative")
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

    def _fallback_response(self, yearly, price_change_pct) -> str:
        latest = int(yearly.iloc[-1]["median_price"])
        return (
            f"HDB resale flat prices have changed by {price_change_pct:.1f}% over the period analysed. "
            f"The current median resale price stands at SGD {latest:,}. "
            f"Demand remains strong across most towns, with mature estates continuing to attract premium valuations."
        )
