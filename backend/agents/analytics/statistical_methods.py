"""
Advanced statistical methods for employment analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def analyze_correlations(df: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
    """Analyze correlations between sectors"""
    try:
        # Pivot data to get sectors as columns
        pivot_data = sector_trends.pivot_table(
            values='employment_count',
            index='year',
            columns='sector'
        )
        
        # Calculate correlation matrix
        correlation_matrix = pivot_data.corr()
        
        # Find strong correlations (> 0.7 or < -0.7)
        strong_correlations = []
        sectors = correlation_matrix.columns.tolist()
        
        for i, sector1 in enumerate(sectors):
            for j, sector2 in enumerate(sectors):
                if i < j:  # Avoid duplicates
                    corr_value = correlation_matrix.loc[sector1, sector2]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            "sector1": sector1,
                            "sector2": sector2,
                            "correlation": round(corr_value, 3),
                            "strength": "strong positive" if corr_value > 0.7 else "strong negative",
                            "interpretation": f"{sector1} and {sector2} show {'similar' if corr_value > 0 else 'opposite'} growth patterns"
                        })
        
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "summary": f"Found {len(strong_correlations)} strong correlations between sectors"
        }
        
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        return {}

def perform_statistical_analysis(df: pd.DataFrame, yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
    """Perform comprehensive statistical analysis"""
    try:
        analysis = {
            "descriptive_statistics": {},
            "variance_analysis": {},
            "growth_metrics": {},
            "sector_statistics": {}
        }
        
        # Descriptive statistics
        analysis["descriptive_statistics"] = {
            "mean": float(yearly_trends['employment_count'].mean()),
            "median": float(yearly_trends['employment_count'].median()),
            "std_deviation": float(yearly_trends['employment_count'].std()),
            "variance": float(yearly_trends['employment_count'].var()),
            "min": float(yearly_trends['employment_count'].min()),
            "max": float(yearly_trends['employment_count'].max()),
            "range": float(yearly_trends['employment_count'].max() - yearly_trends['employment_count'].min()),
            "coefficient_of_variation": float((yearly_trends['employment_count'].std() / yearly_trends['employment_count'].mean()) * 100)
        }
        
        # Variance analysis
        growth_rates = yearly_trends['growth_rate'].dropna()
        if len(growth_rates) > 0:
            analysis["variance_analysis"] = {
                "growth_rate_mean": float(growth_rates.mean()),
                "growth_rate_std": float(growth_rates.std()),
                "growth_rate_variance": float(growth_rates.var()),
                "growth_stability": "stable" if growth_rates.std() < 2 else "volatile"
            }
        
        # Growth metrics
        if len(yearly_trends) >= 2:
            first_value = yearly_trends.iloc[0]['employment_count']
            last_value = yearly_trends.iloc[-1]['employment_count']
            years = len(yearly_trends) - 1
            
            # Compound Annual Growth Rate (CAGR)
            cagr = (pow(last_value / first_value, 1/years) - 1) * 100
            
            analysis["growth_metrics"] = {
                "total_growth_pct": float(((last_value - first_value) / first_value) * 100),
                "absolute_growth": float(last_value - first_value),
                "cagr": float(cagr),
                "years_analyzed": years + 1
            }
        
        # Sector-specific statistics
        sectors = sector_trends['sector'].unique()
        sector_stats = {}
        
        for sector in sectors:
            sector_data = sector_trends[sector_trends['sector'] == sector]
            if len(sector_data) >= 2:
                sector_first = sector_data.iloc[0]['employment_count']
                sector_last = sector_data.iloc[-1]['employment_count']
                sector_growth = ((sector_last - sector_first) / sector_first) * 100
                
                sector_stats[sector] = {
                    "mean_employment": float(sector_data['employment_count'].mean()),
                    "total_growth_pct": float(sector_growth),
                    "std_deviation": float(sector_data['employment_count'].std()),
                    "trend": "growing" if sector_growth > 0 else "declining"
                }
        
        analysis["sector_statistics"] = sector_stats
        
        return analysis
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        return {}

def detect_patterns(yearly_trends: pd.DataFrame, sector_trends: pd.DataFrame) -> Dict[str, Any]:
    """Detect patterns in employment data"""
    try:
        patterns = {
            "overall_trend": "",
            "growth_pattern": "",
            "volatility": "",
            "sector_patterns": [],
            "anomalies": []
        }
        
        # Overall trend detection
        growth_rates = yearly_trends['growth_rate'].dropna()
        if len(growth_rates) > 0:
            avg_growth = growth_rates.mean()
            if avg_growth > 5:
                patterns["overall_trend"] = "strong upward trend"
            elif avg_growth > 2:
                patterns["overall_trend"] = "moderate upward trend"
            elif avg_growth > -2:
                patterns["overall_trend"] = "stable"
            else:
                patterns["overall_trend"] = "declining trend"
        
        # Growth pattern (accelerating, decelerating, consistent)
        if len(growth_rates) >= 3:
            first_half_avg = growth_rates.iloc[:len(growth_rates)//2].mean()
            second_half_avg = growth_rates.iloc[len(growth_rates)//2:].mean()
            
            if second_half_avg > first_half_avg + 1:
                patterns["growth_pattern"] = "accelerating"
            elif second_half_avg < first_half_avg - 1:
                patterns["growth_pattern"] = "decelerating"
            else:
                patterns["growth_pattern"] = "consistent"
        
        # Volatility assessment
        if len(growth_rates) > 0:
            std_dev = growth_rates.std()
            if std_dev < 2:
                patterns["volatility"] = "low - stable growth"
            elif std_dev < 5:
                patterns["volatility"] = "moderate - some fluctuation"
            else:
                patterns["volatility"] = "high - significant variation"
        
        # Sector patterns
        sectors = sector_trends['sector'].unique()
        for sector in sectors:
            sector_data = sector_trends[sector_trends['sector'] == sector]
            if len(sector_data) >= 2:
                sector_first = sector_data.iloc[0]['employment_count']
                sector_last = sector_data.iloc[-1]['employment_count']
                sector_growth = ((sector_last - sector_first) / sector_first) * 100
                
                pattern_desc = ""
                if sector_growth > 30:
                    pattern_desc = "rapid expansion"
                elif sector_growth > 15:
                    pattern_desc = "strong growth"
                elif sector_growth > 5:
                    pattern_desc = "moderate growth"
                elif sector_growth > -5:
                    pattern_desc = "stable"
                else:
                    pattern_desc = "contraction"
                
                patterns["sector_patterns"].append({
                    "sector": sector,
                    "pattern": pattern_desc,
                    "growth_pct": round(sector_growth, 2)
                })
        
        # Detect anomalies (outliers in growth rates)
        if len(growth_rates) > 0:
            Q1 = growth_rates.quantile(0.25)
            Q3 = growth_rates.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            for idx, row in yearly_trends.iterrows():
                if pd.notna(row['growth_rate']):
                    if row['growth_rate'] < lower_bound or row['growth_rate'] > upper_bound:
                        patterns["anomalies"].append({
                            "year": int(row['year']),
                            "growth_rate": round(row['growth_rate'], 2),
                            "type": "unusually high" if row['growth_rate'] > upper_bound else "unusually low"
                        })
        
        return patterns
        
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}")
        return {}
