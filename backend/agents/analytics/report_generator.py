"""
Report Generator for structured reports with citations
"""
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate structured reports with proper citations and formatting"""
    
    def __init__(self):
        self.data_source_urls = {
            "data.gov.sg": "https://data.gov.sg/datasets/d_d2518fed6cc2014f0cd061b4570a9592/view",
            "MOM Statistics": "https://stats.mom.gov.sg/Pages/EmploymentTimeSeries.aspx",
            "DOS SingStat": "https://www.singstat.gov.sg/find-data/search-by-theme/population/population-and-population-structure/latest-data"
        }
    
    def generate_structured_report(
        self, 
        query: str,
        analysis_result: Dict[str, Any],
        extraction_info: Dict[str, Any],
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a complete structured report with citations"""
        
        report = {
            "title": self._generate_title(query, parsed_query),
            "generated_date": datetime.now().isoformat(),
            "query": query,
            
            # Executive Summary
            "executive_summary": analysis_result.get('conversational_response', ''),
            
            # Data Sources with Citations
            "data_sources": self._format_citations(extraction_info),
            
            # Methodology
            "methodology": self._generate_methodology(parsed_query),
            
            # Findings
            "findings": {
                "overview": self._generate_findings_overview(analysis_result),
                "yearly_trends": analysis_result.get('yearly_trends', []),
                "sector_analysis": analysis_result.get('sector_trends', []),
                "statistical_analysis": analysis_result.get('statistical_analysis', {}),
                "correlations": analysis_result.get('correlations', {}),
                "key_insights": analysis_result.get('insights', [])
            },
            
            # Visualizations
            "visualizations": self._format_visualizations(analysis_result),
            
            # Summary Statistics
            "summary_statistics": analysis_result.get('summary_statistics', {}),
            
            # Recommendations
            "recommendations": self._generate_recommendations(analysis_result),
            
            # Metadata
            "metadata": {
                "report_version": "1.0",
                "analysis_type": parsed_query.get('analysis', 'trend'),
                "time_period": parsed_query.get('year_range', ''),
                "total_records_analyzed": extraction_info.get('records_count', 0),
                "data_quality_score": extraction_info.get('quality_score', 0)
            }
        }
        
        return report
    
    def _generate_title(self, query: str, parsed_query: Dict[str, Any]) -> str:
        """Generate a formal report title"""
        year_range = parsed_query.get('year_range', '') or ''
        analysis_type = parsed_query.get('analysis', 'Analysis') or 'Analysis'
        
        # Ensure analysis_type is a string and capitalize it
        analysis_type_str = str(analysis_type).strip() if analysis_type else 'Analysis'
        
        if year_range:
            return f"Employment {analysis_type_str.title()} Analysis: {year_range}"
        else:
            return f"Employment {analysis_type_str.title()} Analysis"
    
    def _format_citations(self, extraction_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format data source citations in APA style"""
        citations = []
        sources_loaded = extraction_info.get('sources_loaded', [])
        
        for source in sources_loaded:
            citation_entry = {
                "source_name": "",
                "dataset": "",
                "url": "",
                "access_date": datetime.now().strftime("%B %d, %Y"),
                "records_used": 0,
                "citation_apa": ""
            }
            
            if 'data.gov.sg' in source:
                citation_entry.update({
                    "source_name": "Singapore Open Data Portal",
                    "dataset": "Employment by Sector (Annual)",
                    "url": self.data_source_urls["data.gov.sg"],
                    "records_used": extraction_info.get('records_count', 0),
                    "citation_apa": f"Singapore Open Data Portal. (2024). Employment by Sector. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {self.data_source_urls['data.gov.sg']}"
                })
                citations.append(citation_entry)
                
            elif 'MOM' in source:
                citation_entry.update({
                    "source_name": "Ministry of Manpower Singapore",
                    "dataset": "Annual Employment Change by Industry",
                    "url": self.data_source_urls["MOM Statistics"],
                    "records_used": extraction_info.get('records_count', 0),
                    "citation_apa": f"Ministry of Manpower. (2024). Employment Time Series. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {self.data_source_urls['MOM Statistics']}"
                })
                citations.append(citation_entry)
                
            elif 'SingStat' in source:
                citation_entry.update({
                    "source_name": "Department of Statistics Singapore",
                    "dataset": "Population and Employment Statistics",
                    "url": self.data_source_urls["DOS SingStat"],
                    "records_used": extraction_info.get('records_count', 0),
                    "citation_apa": f"Department of Statistics Singapore. (2024). Population and Employment Data. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {self.data_source_urls['DOS SingStat']}"
                })
                citations.append(citation_entry)
        
        return citations
    
    def _generate_methodology(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Generate methodology documentation"""
        return {
            "overview": "This analysis employs quantitative methods to examine employment trends using official government data sources.",
            "data_collection": {
                "sources": "Data was collected from multiple Singapore government databases including data.gov.sg, Ministry of Manpower (MOM), and Department of Statistics (DOS).",
                "time_period": parsed_query.get('year_range', '2020-2024'),
                "data_types": "Employment counts, sector classifications, and temporal data"
            },
            "analytical_methods": [
                {
                    "method": "Trend Analysis",
                    "description": "Year-over-year employment trends calculated using time series analysis"
                },
                {
                    "method": "Growth Rate Calculation",
                    "description": "Percentage change computed using period-over-period comparison"
                },
                {
                    "method": "Sector Aggregation",
                    "description": "Employment data grouped by industry sector for comparative analysis"
                },
                {
                    "method": "Correlation Analysis",
                    "description": "Pearson correlation coefficients calculated to identify relationships between sectors"
                },
                {
                    "method": "Statistical Summary",
                    "description": "Descriptive statistics including mean, median, standard deviation, and growth rates"
                }
            ],
            "data_quality": {
                "validation": "Data validated for completeness, consistency, and accuracy",
                "cleaning": "Duplicate records removed, missing values handled, outliers identified",
                "limitations": "Analysis limited to available government data; some subsectors may have incomplete historical records"
            },
            "tools_used": [
                "Python 3.9+ for data processing",
                "Pandas for statistical analysis",
                "LangGraph for workflow orchestration",
                "LLM (Mistral AI) for insight generation"
            ]
        }
    
    def _generate_findings_overview(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a findings overview paragraph"""
        stats = analysis_result.get('summary_statistics', {})
        avg_growth = stats.get('avg_annual_growth', 0)
        total_years = stats.get('total_years', 0)
        
        return f"""The analysis reveals consistent employment growth over the {total_years}-year period examined, 
with an average annual growth rate of {avg_growth:.2f}%. Employment patterns show variation across sectors, 
with some industries demonstrating stronger growth trajectories than others. The data indicates overall 
positive trends in the labor market, though sector-specific dynamics warrant detailed examination for 
policy planning purposes."""
    
    def _format_visualizations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format visualization metadata"""
        visualizations = []
        
        if analysis_result.get('chart'):
            visualizations.append({
                "type": "line_chart",
                "title": "Employment Trends Over Time",
                "description": "Year-over-year employment trends showing overall and sector-specific patterns",
                "format": "base64_png",
                "data": analysis_result['chart']
            })
        
        if analysis_result.get('correlation_heatmap'):
            visualizations.append({
                "type": "heatmap",
                "title": "Sector Correlation Matrix",
                "description": "Correlation coefficients between different employment sectors",
                "format": "base64_png",
                "data": analysis_result['correlation_heatmap']
            })
        
        return visualizations
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate policy recommendations based on analysis"""
        recommendations = []
        
        stats = analysis_result.get('summary_statistics', {})
        sector_trends = analysis_result.get('sector_trends', [])
        
        # Analyze growth patterns
        if stats.get('avg_annual_growth', 0) > 5:
            recommendations.append({
                "category": "Workforce Development",
                "priority": "High",
                "recommendation": "Sustain current employment growth momentum through continued investment in skills training and workforce development programs.",
                "rationale": f"Average annual growth of {stats.get('avg_annual_growth', 0):.2f}% indicates strong labor market expansion."
            })
        
        # Sector-specific recommendations
        if sector_trends:
            # Find high-growth sectors
            sector_growth = {}
            for trend in sector_trends:
                sector = trend.get('sector')
                if sector and sector not in sector_growth:
                    sector_growth[sector] = []
                if 'employment_count' in trend:
                    sector_growth[sector].append(trend['employment_count'])
            
            for sector, values in sector_growth.items():
                if len(values) >= 2:
                    growth = ((values[-1] - values[0]) / values[0]) * 100
                    if growth > 20:
                        recommendations.append({
                            "category": "Sector Development",
                            "priority": "Medium",
                            "recommendation": f"Expand support programs for the {sector} sector to capitalize on strong growth trajectory.",
                            "rationale": f"{sector} sector shows {growth:.1f}% growth, indicating significant expansion potential."
                        })
        
        # General recommendations
        recommendations.append({
            "category": "Data Monitoring",
            "priority": "Medium",
            "recommendation": "Continue regular monitoring of employment trends across all sectors to identify emerging patterns and potential challenges.",
            "rationale": "Ongoing data collection enables proactive policy responses to labor market changes."
        })
        
        recommendations.append({
            "category": "Policy Planning",
            "priority": "High",
            "recommendation": "Develop sector-specific employment strategies based on observed growth patterns and correlations.",
            "rationale": "Tailored approaches can maximize employment outcomes in high-potential sectors."
        })
        
        return recommendations
