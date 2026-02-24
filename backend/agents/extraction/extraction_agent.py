import pandas as pd
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger(__name__)

class ExtractionAgent:
    """Data Extraction Agent for loading and processing government datasets"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_cache = {}
        self.data_sources = {
            "data.gov.sg": "employment.csv",
            "MOM Statistics": "mom_employment_annual.csv",
            "DOS SingStat": "singstat_population.json",
            "Internal Database": "datagov_employment_sectors.xlsx"
        }
        self.validation_errors = []
    
    def load_employment_data(self) -> Dict[str, Any]:
        """Load employment data from multiple sources with error handling"""
        all_data = []
        sources_loaded = []
        errors = []
        
        # Source 1: data.gov.sg CSV
        try:
            csv_result = self._load_csv_data("employment.csv", "data.gov.sg")
            if csv_result["status"] == "success":
                all_data.extend(csv_result["data"])
                sources_loaded.append("data.gov.sg (CSV)")
                logger.info(f"Loaded {len(csv_result['data'])} records from data.gov.sg")
        except Exception as e:
            error_msg = f"data.gov.sg CSV failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        # Source 2: MOM Statistics CSV
        try:
            mom_result = self._load_mom_data("mom_employment_annual.csv")
            if mom_result["status"] == "success":
                all_data.extend(mom_result["data"])
                sources_loaded.append("MOM Statistics (CSV)")
                logger.info(f"Loaded {len(mom_result['data'])} records from MOM")
        except Exception as e:
            error_msg = f"MOM Statistics CSV failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        # Source 3: DOS SingStat JSON
        try:
            json_result = self._load_json_data("singstat_population.json", "DOS SingStat")
            if json_result["status"] == "success":
                sources_loaded.append("DOS SingStat (JSON)")
                logger.info(f"Loaded population data from SingStat")
        except Exception as e:
            error_msg = f"SingStat JSON failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        if not all_data:
            return {
                "status": "error",
                "error": "No data could be loaded from any source",
                "errors": errors,
                "data_info": {},
                "data": []
            }
        
        # Combine and validate data
        df = pd.DataFrame(all_data)
        df = self._clean_data(df)
        
        # Data quality validation
        validation_report = self._validate_data_quality(df)
        
        data_info = {
            "sources_loaded": sources_loaded,
            "total_records": len(df),
            "years_covered": f"{df['year'].min()}-{df['year'].max()}",
            "sectors": df['sector'].unique().tolist() if 'sector' in df.columns else [],
            "subsectors": df['subsector'].unique().tolist() if 'subsector' in df.columns else [],
            "columns": df.columns.tolist(),
            "validation_report": validation_report,
            "errors": errors if errors else None
        }
        
        self.data_cache["employment"] = df
        
        return {
            "status": "success",
            "data_info": data_info,
            "data": df.to_dict('records')
        }
    
    def _load_csv_data(self, filename: str, source: str) -> Dict[str, Any]:
        """Load CSV data with error handling"""
        try:
            csv_path = self.data_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"File not found: {csv_path}")
            
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV from {source}: {len(df)} rows")
            
            return {
                "status": "success",
                "data": df.to_dict('records'),
                "source": source
            }
        except Exception as e:
            logger.error(f"CSV load failed for {filename}: {e}")
            return {"status": "error", "error": str(e), "data": []}
    
    def _load_mom_data(self, filename: str) -> Dict[str, Any]:
        """Load MOM Statistics CSV with specific handling"""
        try:
            csv_path = self.data_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"MOM data not found: {csv_path}")
            
            df = pd.read_csv(csv_path)
            
            # Transform MOM data to match our schema
            if 'industry1' in df.columns:
                df = df.rename(columns={'industry1': 'sector'})
            if 'industry3' in df.columns:
                df = df.rename(columns={'industry3': 'subsector'})
            
            # Filter recent years
            if 'year' in df.columns:
                df = df[df['year'] >= 2020]
            
            logger.info(f"Loaded MOM data: {len(df)} rows")
            
            return {
                "status": "success",
                "data": df.to_dict('records'),
                "source": "MOM Statistics"
            }
        except Exception as e:
            logger.error(f"MOM data load failed: {e}")
            return {"status": "error", "error": str(e), "data": []}
    
    def _load_json_data(self, filename: str, source: str) -> Dict[str, Any]:
        """Load JSON data with error handling"""
        try:
            json_path = self.data_dir / filename
            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_path}")
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Cache population data separately
            if 'data' in data:
                self.data_cache["population"] = data['data']
            
            logger.info(f"Loaded JSON from {source}")
            
            return {
                "status": "success",
                "data": data.get('data', []),
                "source": source
            }
        except Exception as e:
            logger.error(f"JSON load failed for {filename}: {e}")
            return {"status": "error", "error": str(e), "data": []}
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality validation"""
        validation = {
            "total_records": len(df),
            "duplicate_records": df.duplicated().sum(),
            "missing_values": {},
            "data_types": {},
            "outliers": {},
            "quality_score": 0.0
        }
        
        # Check missing values
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                validation["missing_values"][col] = {
                    "count": int(missing_count),
                    "percentage": round(missing_count / len(df) * 100, 2)
                }
        
        # Check data types
        for col in df.columns:
            validation["data_types"][col] = str(df[col].dtype)
        
        # Check for outliers in numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                validation["outliers"][col] = len(outliers)
        
        # Calculate quality score
        completeness = 1 - (sum([v['count'] for v in validation['missing_values'].values()]) / (len(df) * len(df.columns)))
        uniqueness = 1 - (validation['duplicate_records'] / len(df)) if len(df) > 0 else 0
        validation["quality_score"] = round((completeness + uniqueness) / 2 * 100, 2)
        
        return validation
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the data with comprehensive error handling"""
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates()
        duplicates_removed = original_count - len(df)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate records")
        
        # Handle missing values strategically
        critical_cols = ['year', 'sector']
        for col in critical_cols:
            if col in df.columns:
                before = len(df)
                df = df.dropna(subset=[col])
                after = len(df)
                if before != after:
                    logger.warning(f"Dropped {before - after} rows with missing {col}")
        
        # Convert year to integer
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df = df.dropna(subset=['year'])
            df['year'] = df['year'].astype(int)
        
        # Convert employment_count to numeric
        if 'employment_count' in df.columns:
            df['employment_count'] = pd.to_numeric(df['employment_count'], errors='coerce')
            df = df.dropna(subset=['employment_count'])
            df['employment_count'] = df['employment_count'].astype(int)
        
        # Handle employment_change
        if 'employment_change' in df.columns:
            df['employment_change'] = pd.to_numeric(df['employment_change'], errors='coerce')
        
        # Standardize text fields
        text_cols = ['sector', 'subsector', 'source']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Sort by year and sector
        sort_cols = ['year']
        if 'sector' in df.columns:
            sort_cols.append('sector')
        df = df.sort_values(sort_cols)
        
        logger.info(f"Data cleaning complete: {len(df)} records after cleaning")
        
        return df
    
    def get_data_summary(self, dataset: str = "employment") -> Dict[str, Any]:
        """Get summary statistics for the dataset"""
        if dataset not in self.data_cache:
            if dataset == "employment":
                self.load_employment_data()
            else:
                return {"error": f"Dataset {dataset} not available"}
        
        df = self.data_cache[dataset]
        
        summary = {
            "total_records": len(df),
            "date_range": {
                "start": df['year'].min(),
                "end": df['year'].max()
            },
            "sectors": df['sector'].unique().tolist(),
            "total_employment_by_year": df.groupby('year')['employment_count'].sum().to_dict(),
            "employment_by_sector": df.groupby('sector')['employment_count'].mean().to_dict()
        }
        
        return summary
