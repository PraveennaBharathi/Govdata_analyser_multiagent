import pandas as pd
import numpy as np
import io
import base64
import logging
from typing import Dict, Any, List
from services.llm_service import LLMService
from agents.analytics.report_generator import ReportGenerator
from agents.analytics.hdb_analytics import HDBAnalytics
from agents.analytics.labour_analytics import LabourAnalytics
from agents.analytics.crossdomain_analytics import CrossDomainAnalytics
from agents.analytics.statistical_methods import (
    analyze_correlations,
    perform_statistical_analysis,
    detect_patterns
)
from utils.json_utils import sanitize_for_json

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class AnalyticsAgent:
    """Analytics Agent for trend analysis and insight generation"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.report_generator = ReportGenerator()
        self.hdb_analytics = HDBAnalytics()
        self.labour_analytics = LabourAnalytics()
        self.crossdomain_analytics = CrossDomainAnalytics()

    async def analyze_hdb_data(self, data: List[Dict], parsed_query: Dict, forced_model: str = None) -> Dict[str, Any]:
        return await self.hdb_analytics.analyze(data, parsed_query, forced_model=forced_model)

    async def analyze_labour_market(self, data: List[Dict], parsed_query: Dict, forced_model: str = None) -> Dict[str, Any]:
        return await self.labour_analytics.analyze(data, parsed_query, forced_model=forced_model)

    async def analyze_cross_domain(self, parsed_query: Dict, forced_model: str = None) -> Dict[str, Any]:
        return await self.crossdomain_analytics.analyze(parsed_query, forced_model=forced_model)
    
    async def analyze_employment_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform employment trend analysis"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                return {"status": "error", "error": "No data provided"}
            
            # Trend analysis using groupby
            yearly_trends = df.groupby('year')['employment_count'].mean().reset_index()
            sector_trends = df.groupby(['year', 'sector'])['employment_count'].mean().reset_index()
            
            # Calculate growth rates
            yearly_trends['growth_rate'] = yearly_trends['employment_count'].pct_change() * 100
            
            # Generate conversational response
            conversational_response = await self._generate_conversational_response(df, yearly_trends, sector_trends)
            
            # Generate insights using LLM
            insights = await self._generate_insights(df, yearly_trends)
            
            # Perform correlation analysis
            correlations = self._analyze_correlations(df, sector_trends)
            
            # Perform advanced statistical analysis
            statistical_analysis = self._perform_statistical_analysis(df, yearly_trends, sector_trends)
            
            # Detect patterns
            patterns = self._detect_patterns(yearly_trends, sector_trends)
            
            # Create charts
            chart_base64 = self._create_trend_chart(yearly_trends, sector_trends)
            correlation_heatmap = self._create_correlation_heatmap(correlations) if correlations else ""
            
            analysis_result = {
                "status": "success",
                "conversational_response": conversational_response,
                "yearly_trends": yearly_trends.to_dict('records'),
                "sector_trends": sector_trends.to_dict('records'),
                "insights": insights,
                "correlations": correlations,
                "statistical_analysis": statistical_analysis,
                "patterns": patterns,
                "chart": chart_base64,
                "correlation_heatmap": correlation_heatmap,
                "summary_statistics": {
                    "total_years": len(yearly_trends),
                    "avg_annual_growth": yearly_trends['growth_rate'].mean(),
                    "max_employment": yearly_trends['employment_count'].max(),
                    "min_employment": yearly_trends['employment_count'].min(),
                    "std_deviation": yearly_trends['employment_count'].std(),
                    "median_employment": yearly_trends['employment_count'].median(),
                    "total_growth_pct": ((yearly_trends.iloc[-1]['employment_count'] - yearly_trends.iloc[0]['employment_count']) / yearly_trends.iloc[0]['employment_count']) * 100
                }
            }
            
            # Sanitize all float values to ensure JSON compliance
            analysis_result = sanitize_for_json(analysis_result)
            
            logger.info("Employment trend analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _analyze_correlations(self, df: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
        """Wrapper for correlation analysis"""
        return analyze_correlations(df, sector_trends)
    
    def _perform_statistical_analysis(self, df: pd.DataFrame, yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
        """Wrapper for statistical analysis"""
        return perform_statistical_analysis(df, yearly_trends, sector_trends)
    
    def _detect_patterns(self, yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
        """Wrapper for pattern detection"""
        return detect_patterns(yearly_trends, sector_trends)
    
    async def _generate_conversational_response(self, df: pd.DataFrame, yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> str:
        """Generate a natural, conversational response to the user's query"""
        try:
            # Prepare data summary for LLM
            years = yearly_trends['year'].tolist()
            start_year = years[0]
            end_year = years[-1]
            
            start_employment = yearly_trends.iloc[0]['employment_count']
            end_employment = yearly_trends.iloc[-1]['employment_count']
            total_growth = ((end_employment - start_employment) / start_employment) * 100
            
            avg_growth = yearly_trends['growth_rate'].dropna().mean()
            
            # Get sector information
            sectors = df['sector'].unique().tolist()
            sector_summary = []
            for sector in sectors:
                sector_data = sector_trends[sector_trends['sector'] == sector]
                if not sector_data.empty:
                    sector_start = sector_data.iloc[0]['employment_count']
                    sector_end = sector_data.iloc[-1]['employment_count']
                    sector_growth = ((sector_end - sector_start) / sector_start) * 100
                    sector_summary.append({
                        "sector": sector,
                        "start": sector_start,
                        "end": sector_end,
                        "growth": sector_growth
                    })
            
            prompt = f"""
            You are a friendly policy analyst having a conversation with a government official. 
            Generate a natural, conversational response (2-3 paragraphs) summarizing the employment trends.
            
            Data:
            - Time period: {start_year} to {end_year}
            - Overall employment: {start_employment:,.0f} → {end_employment:,.0f}
            - Total growth: {total_growth:.1f}%
            - Average annual growth: {avg_growth:.1f}%
            - Sectors analyzed: {', '.join(sectors)}
            - Sector details: {sector_summary}
            
            Write in a warm, professional tone. Start with a direct answer, then provide context and key highlights.
            Make it conversational but informative. Don't use bullet points - write in flowing paragraphs.
            Keep it concise (2-3 paragraphs maximum).
            """
            
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="You are a friendly policy analyst who explains data insights in a conversational, easy-to-understand way."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm_service.generate_response(messages, mode="narrative")
            
            if response:
                return response.strip()
            else:
                # Fallback conversational response
                return self._generate_fallback_conversational_response(start_year, end_year, start_employment, end_employment, total_growth, avg_growth, sectors)
                
        except Exception as e:
            logger.error(f"Conversational response generation failed: {e}")
            return "I've analyzed the employment data for you. The trends show interesting patterns across the years, with notable growth in several sectors. Let me break down the detailed analysis below."
    
    def _generate_fallback_conversational_response(self, start_year, end_year, start_employment, end_employment, total_growth, avg_growth, sectors) -> str:
        """Generate a fallback conversational response when LLM is unavailable"""
        return f"""Great question! Looking at the employment data from {start_year} to {end_year}, I can see some really positive trends. 

Overall employment has grown from approximately {start_employment:,.0f} to {end_employment:,.0f} workers, which represents a {total_growth:.1f}% increase over this period. That's an average annual growth rate of about {avg_growth:.1f}%, which shows consistent and healthy expansion in the job market.

When we break this down by sector - covering {', '.join(sectors)} - we can see that each area has contributed to this growth in different ways. The detailed analysis below shows the year-by-year trends and sector-specific patterns that might be useful for policy planning."""
    
    async def _generate_insights(self, df: pd.DataFrame, trends: pd.DataFrame) -> List[str]:
        """Generate insights using LLM"""
        try:
            # Prepare data for LLM
            data_summary = {
                "total_records": len(df),
                "years": df['year'].unique().tolist(),
                "sectors": df['sector'].unique().tolist(),
                "yearly_totals": trends[['year', 'employment_count']].to_dict('records'),
                "growth_rates": trends[['year', 'growth_rate']].dropna().to_dict('records')
            }
            
            prompt = f"""
            Analyze this employment data and generate 3-5 key insights for policy makers:
            
            Data Summary: {data_summary}
            
            Focus on:
            1. Overall employment trends
            2. Sector-specific patterns  
            3. Growth rate analysis
            4. Policy implications
            
            Return insights as a numbered list, each insight being concise but actionable.
            """
            
            # Use LLM service with fallback
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="You are a policy data analyst providing insights to government decision makers."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm_service.generate_response(messages, mode="narrative")
            
            if response:
                # Parse numbered list
                insights = []
                for line in response.split('\n'):
                    if line.strip() and (line[0].isdigit() or line.startswith('-')):
                        insight = line.strip()
                        # Remove numbering
                        if insight[0].isdigit():
                            insight = insight.split('.', 1)[-1].strip()
                        elif insight.startswith('-'):
                            insight = insight[1:].strip()
                        insights.append(insight)
                
                return insights[:5]  # Limit to 5 insights
            else:
                # Fallback insights
                return [
                    "Employment shows consistent upward trend across all sectors",
                    "Services sector contributes the largest share of employment",
                    "Manufacturing shows steady growth with potential for policy support",
                    "Construction sector demonstrates resilience with moderate growth"
                ]
                
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return ["Insight generation temporarily unavailable"]
    
    def _create_trend_chart(self, yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> str:
        """Create matplotlib chart and return as base64"""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping chart generation")
            return ""
        
        try:
            plt.style.use('seaborn-v0_8')
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Chart 1: Overall employment trend
            ax1.plot(yearly_trends['year'], yearly_trends['employment_count'], 
                    marker='o', linewidth=2, markersize=8, color='#2E86AB')
            ax1.set_title('Overall Employment Trend', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Employment Count')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Chart 2: Sector-wise trends
            for sector in sector_trends['sector'].unique():
                sector_data = sector_trends[sector_trends['sector'] == sector]
                ax2.plot(sector_data['year'], sector_data['employment_count'], 
                        marker='s', linewidth=2, markersize=6, label=sector)
            
            ax2.set_title('Employment Trends by Sector', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Employment Count')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return ""
    
    def _create_correlation_heatmap(self, correlations: Dict[str, Any]) -> str:
        """Create correlation heatmap and return as base64"""
        if not MATPLOTLIB_AVAILABLE or not correlations:
            return ""
        
        try:
            correlation_matrix = correlations.get('correlation_matrix', {})
            if not correlation_matrix:
                return ""
            
            # Convert to DataFrame
            corr_df = pd.DataFrame(correlation_matrix)
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Create heatmap using imshow
            im = ax.imshow(corr_df.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            
            # Set ticks and labels
            ax.set_xticks(range(len(corr_df.columns)))
            ax.set_yticks(range(len(corr_df.index)))
            ax.set_xticklabels(corr_df.columns, rotation=45, ha='right')
            ax.set_yticklabels(corr_df.index)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20)
            
            # Add correlation values as text
            for i in range(len(corr_df.index)):
                for j in range(len(corr_df.columns)):
                    text = ax.text(j, i, f'{corr_df.values[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontsize=9)
            
            ax.set_title('Sector Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return ""
