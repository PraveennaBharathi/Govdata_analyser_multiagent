# Data Sources Documentation

## Overview
This document describes the government data sources integrated into the Agentic Policy Data Analytics Platform.

## Data Sources

### 1. Data.gov.sg - Employment by Sector (CSV)
- **File**: `employment.csv`
- **Source**: Singapore Open Data Platform
- **Format**: CSV
- **Coverage**: 2020-2024
- **Records**: 75 records
- **Fields**:
  - `year`: Year of data collection
  - `sector`: Main employment sector (Manufacturing, Services, Construction)
  - `subsector`: Detailed subsector classification
  - `employment_count`: Number of employed persons
  - `employment_change`: Year-over-year change percentage
  - `source`: Data source identifier

**Sectors Covered**:
- **Manufacturing**: Electronics, Biomedical, Precision Engineering, Chemicals, Food & Beverage
- **Services**: Financial Services, Information & Communications, Professional Services, Healthcare, Education, Retail, F&B Services
- **Construction**: Building Construction, Civil Engineering, Specialty Trade

### 2. MOM (Ministry of Manpower) Statistics (CSV)
- **File**: `mom_employment_annual.csv`
- **Source**: Ministry of Manpower - Manpower Research & Statistics Department
- **URL**: https://stats.mom.gov.sg/iMAS_Tables1/CSV/mrsd_4_annl_emp_chg_by_ind_28042025.csv
- **Format**: CSV
- **Coverage**: 1991-2024 (filtered to 2020+ for analysis)
- **Records**: 1,010 total records
- **Fields**:
  - `year`: Year of data
  - `industry1`: Primary industry classification
  - `industry2`: Secondary industry classification
  - `industry3`: Detailed industry classification
  - `employment_change`: Annual employment change (thousands)

**Data Characteristics**:
- Administrative records with Labour Force Survey estimates for self-employed
- Industry classification based on SSIC 2020 from 2008 onwards
- Includes granular industry breakdowns

### 3. DOS SingStat - Population & Employment (JSON)
- **File**: `singstat_population.json`
- **Source**: Department of Statistics Singapore (DOS)
- **Format**: JSON
- **Coverage**: 2020-2024
- **Records**: 5 years of population data

**Structure**:
```json
{
  "metadata": {
    "source": "DOS SingStat",
    "dataset": "Population and Demographics",
    "last_updated": "2024-12-31"
  },
  "data": [
    {
      "year": 2024,
      "total_population": 5988000,
      "working_age_population": 3950000,
      "employment_rate": 69.8,
      "unemployment_rate": 1.8,
      "age_groups": {...}
    }
  ]
}
```

**Fields**:
- Population statistics by age group
- Employment and unemployment rates
- Working age population metrics
- Age group breakdowns (15-24, 25-54, 55-64, 65+)

### 4. Internal Database - Employment Sectors (Excel/CSV)
- **File**: `datagov_employment_sectors.xlsx`
- **Source**: Mock internal database (simulates proprietary data)
- **Format**: Excel/CSV
- **Coverage**: 2020-2024
- **Records**: 75 records with detailed metrics

**Additional Fields**:
- `avg_salary`: Average monthly salary by subsector
- `growth_rate`: Sector-specific growth rates

## Data Quality Metrics

### Validation Checks
1. **Completeness**: Missing value detection and reporting
2. **Consistency**: Data type validation across sources
3. **Accuracy**: Outlier detection using IQR method
4. **Uniqueness**: Duplicate record identification
5. **Timeliness**: Year range validation (2020-2024)

### Data Cleaning Process
1. **Duplicate Removal**: Automatic deduplication
2. **Missing Value Handling**: 
   - Critical fields (year, sector): Records dropped
   - Non-critical fields: Flagged but retained
3. **Type Conversion**: Numeric fields standardized
4. **Text Standardization**: Trimming and case normalization
5. **Outlier Detection**: Statistical analysis for anomalies

### Quality Score Calculation
- **Completeness Score**: (1 - missing_values_ratio) × 100
- **Uniqueness Score**: (1 - duplicate_ratio) × 100
- **Overall Quality**: Average of completeness and uniqueness

## Error Handling

### API Failure Scenarios
1. **File Not Found**: Graceful fallback to available sources
2. **Parse Errors**: Logged with detailed error messages
3. **Network Issues**: Retry mechanism (for future API integration)
4. **Data Format Mismatch**: Schema transformation and validation

### Fallback Strategy
- If primary source fails, system attempts secondary sources
- Minimum 1 source required for analysis
- All errors logged with timestamps and details
- Partial data loading supported

## Data Format Support

| Format | Handler | Use Case |
|--------|---------|----------|
| CSV | `pandas.read_csv()` | Structured tabular data |
| JSON | `json.load()` | Hierarchical/nested data |
| Excel | `pandas.read_excel()` | Multi-sheet workbooks |
| API | `httpx` (future) | Real-time data feeds |

## Usage Example

```python
from agents.extraction.extraction_agent import ExtractionAgent

# Initialize agent
extractor = ExtractionAgent(data_dir="data")

# Load from multiple sources
result = extractor.load_employment_data()

# Check results
print(f"Sources loaded: {result['data_info']['sources_loaded']}")
print(f"Total records: {result['data_info']['total_records']}")
print(f"Quality score: {result['data_info']['validation_report']['quality_score']}")
```

## Data Lineage

```
Government Sources
    ├── data.gov.sg (CSV) ──────┐
    ├── MOM Statistics (CSV) ────┤
    ├── DOS SingStat (JSON) ─────┼──> Extraction Agent ──> Cleaned Dataset ──> Analytics Agent
    └── Internal DB (Excel) ─────┘
```

## Compliance & Attribution

All data sources are properly attributed and used in accordance with:
- Singapore Open Data Licence
- MOM Data Usage Terms
- DOS Statistical Data Guidelines

## Future Enhancements

1. **Real-time API Integration**: Direct API calls to data.gov.sg
2. **Automated Updates**: Scheduled data refresh
3. **Version Control**: Track data source versions
4. **Data Catalog**: Searchable metadata repository
5. **Quality Monitoring**: Automated quality alerts
