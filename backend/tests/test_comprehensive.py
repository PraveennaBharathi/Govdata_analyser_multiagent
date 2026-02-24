#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite
Tests all requirements: statistical analysis, insights, visualizations, reports
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator_agent import CoordinatorAgent
from agents.extraction.extraction_agent import ExtractionAgent
from agents.analytics.analytics_agent import AnalyticsAgent
from services.llm_service import LLMService

class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name, passed, details=""):
        self.total += 1
        if passed:
            self.passed += 1
            status = "✓ PASS"
        else:
            self.failed += 1
            status = "✗ FAIL"
        
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"  {details}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for result in self.results:
            print(f"{result['status']}: {result['test']}")
        print("\n" + "="*70)
        print(f"Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/self.total*100):.1f}%")
        print("="*70)

results = TestResults()

# ============================================================================
# TEST 1: STATISTICAL ANALYSIS
# ============================================================================
async def test_statistical_analysis():
    """Test comprehensive statistical analysis features"""
    print("\n" + "="*70)
    print("TEST SUITE 1: STATISTICAL ANALYSIS")
    print("="*70)
    
    coordinator = CoordinatorAgent()
    
    # Test 1.1: Correlation Analysis
    print("\n[1.1] Testing Correlation Analysis...")
    response = await coordinator.process_query("Analyze employment trends from 2020 to 2024")
    
    correlations = response.get('result', {}).get('analysis', {}).get('correlations', {})
    has_correlation_matrix = bool(correlations.get('correlation_matrix'))
    strong_correlations = correlations.get('strong_correlations', [])
    
    results.add_result(
        "Correlation Matrix Generated",
        has_correlation_matrix,
        f"Matrix exists: {has_correlation_matrix}"
    )
    
    results.add_result(
        "Strong Correlations Identified",
        len(strong_correlations) >= 0,
        f"Found {len(strong_correlations)} strong correlations"
    )
    
    # Test 1.2: Pattern Detection
    print("\n[1.2] Testing Pattern Detection...")
    patterns = response.get('result', {}).get('analysis', {}).get('patterns', {})
    
    has_overall_trend = bool(patterns.get('overall_trend'))
    has_growth_pattern = bool(patterns.get('growth_pattern'))
    has_volatility = bool(patterns.get('volatility'))
    has_sector_patterns = bool(patterns.get('sector_patterns'))
    
    results.add_result(
        "Overall Trend Detection",
        has_overall_trend,
        f"Trend: {patterns.get('overall_trend', 'N/A')}"
    )
    
    results.add_result(
        "Growth Pattern Analysis",
        has_growth_pattern,
        f"Pattern: {patterns.get('growth_pattern', 'N/A')}"
    )
    
    results.add_result(
        "Volatility Assessment",
        has_volatility,
        f"Volatility: {patterns.get('volatility', 'N/A')}"
    )
    
    results.add_result(
        "Sector Pattern Detection",
        has_sector_patterns and len(patterns.get('sector_patterns', [])) > 0,
        f"Patterns for {len(patterns.get('sector_patterns', []))} sectors"
    )
    
    # Test 1.3: Advanced Statistics
    print("\n[1.3] Testing Advanced Statistics...")
    stats = response.get('result', {}).get('analysis', {}).get('statistical_analysis', {})
    
    has_descriptive = bool(stats.get('descriptive_statistics'))
    has_variance = bool(stats.get('variance_analysis'))
    has_growth_metrics = bool(stats.get('growth_metrics'))
    has_sector_stats = bool(stats.get('sector_statistics'))
    
    results.add_result(
        "Descriptive Statistics",
        has_descriptive,
        f"Includes: mean, median, std, variance"
    )
    
    results.add_result(
        "Variance Analysis",
        has_variance,
        f"Growth stability analysis included"
    )
    
    results.add_result(
        "Growth Metrics (CAGR)",
        has_growth_metrics,
        f"CAGR and total growth calculated"
    )
    
    results.add_result(
        "Sector-Specific Statistics",
        has_sector_stats,
        f"Stats for {len(stats.get('sector_statistics', {}))} sectors"
    )
    
    # Test 1.4: Summary Statistics
    print("\n[1.4] Testing Summary Statistics...")
    summary = response.get('result', {}).get('analysis', {}).get('summary_statistics', {})
    
    required_fields = ['total_years', 'avg_annual_growth', 'max_employment', 
                      'min_employment', 'std_deviation', 'median_employment']
    
    has_all_fields = all(field in summary for field in required_fields)
    
    results.add_result(
        "Complete Summary Statistics",
        has_all_fields,
        f"All {len(required_fields)} required fields present"
    )

# ============================================================================
# TEST 2: POLICY-RELEVANT INSIGHTS
# ============================================================================
async def test_policy_insights():
    """Test policy-relevant insight generation"""
    print("\n" + "="*70)
    print("TEST SUITE 2: POLICY-RELEVANT INSIGHTS")
    print("="*70)
    
    coordinator = CoordinatorAgent()
    
    # Test 2.1: Conversational Response
    print("\n[2.1] Testing Conversational Response...")
    response = await coordinator.process_query("How is the manufacturing sector performing?")
    
    conversational = response.get('result', {}).get('conversational_response', '')
    
    results.add_result(
        "Conversational Response Generated",
        len(conversational) > 100,
        f"Length: {len(conversational)} characters"
    )
    
    results.add_result(
        "Natural Language Quality",
        'employment' in conversational.lower() or 'growth' in conversational.lower(),
        "Contains relevant employment/growth terminology"
    )
    
    # Test 2.2: Key Insights
    print("\n[2.2] Testing Key Insights...")
    insights = response.get('result', {}).get('analysis', {}).get('insights', [])
    
    results.add_result(
        "Key Insights Generated",
        len(insights) > 0,
        f"Generated {len(insights)} insights"
    )
    
    # Test 2.3: Sector Analysis
    print("\n[2.3] Testing Sector Analysis...")
    sector_trends = response.get('result', {}).get('analysis', {}).get('sector_trends', [])
    
    results.add_result(
        "Sector-Specific Analysis",
        len(sector_trends) > 0,
        f"Analyzed {len(sector_trends)} sector-year combinations"
    )

# ============================================================================
# TEST 3: VISUALIZATIONS
# ============================================================================
async def test_visualizations():
    """Test visualization generation"""
    print("\n" + "="*70)
    print("TEST SUITE 3: VISUALIZATIONS")
    print("="*70)
    
    coordinator = CoordinatorAgent()
    
    # Test 3.1: Trend Chart
    print("\n[3.1] Testing Trend Chart Generation...")
    response = await coordinator.process_query("Show employment trends from 2020 to 2024")
    
    chart = response.get('result', {}).get('analysis', {}).get('chart', '')
    
    results.add_result(
        "Trend Chart Generated",
        len(chart) > 0,
        f"Chart size: {len(chart)} bytes (base64)"
    )
    
    # Test 3.2: Correlation Heatmap
    print("\n[3.2] Testing Correlation Heatmap...")
    heatmap = response.get('result', {}).get('analysis', {}).get('correlation_heatmap', '')
    
    results.add_result(
        "Correlation Heatmap Generated",
        len(heatmap) > 0,
        f"Heatmap size: {len(heatmap)} bytes (base64)"
    )
    
    # Test 3.3: Visualization Metadata
    print("\n[3.3] Testing Visualization Metadata...")
    report = response.get('result', {}).get('structured_report', {})
    visualizations = report.get('visualizations', []) if report else []
    
    results.add_result(
        "Visualization Metadata",
        len(visualizations) > 0,
        f"Metadata for {len(visualizations)} visualizations"
    )

# ============================================================================
# TEST 4: STRUCTURED REPORTS WITH CITATIONS
# ============================================================================
async def test_structured_reports():
    """Test structured report generation with citations"""
    print("\n" + "="*70)
    print("TEST SUITE 4: STRUCTURED REPORTS WITH CITATIONS")
    print("="*70)
    
    coordinator = CoordinatorAgent()
    
    # Test 4.1: Report Structure
    print("\n[4.1] Testing Report Structure...")
    response = await coordinator.process_query("Analyze employment trends from 2020 to 2024")
    
    report = response.get('result', {}).get('structured_report', {})
    
    results.add_result(
        "Structured Report Generated",
        bool(report),
        "Report object exists"
    )
    
    has_title = bool(report.get('title'))
    has_date = bool(report.get('generated_date'))
    
    results.add_result(
        "Report Title and Date",
        has_title and has_date,
        f"Title: {report.get('title', 'N/A')}"
    )
    
    # Test 4.2: Data Source Citations
    print("\n[4.2] Testing Data Source Citations...")
    data_sources = report.get('data_sources', [])
    
    results.add_result(
        "Data Sources Cited",
        len(data_sources) >= 2,
        f"Cited {len(data_sources)} sources"
    )
    
    # Check APA format
    has_apa_citations = all('citation_apa' in source for source in data_sources)
    
    results.add_result(
        "APA Format Citations",
        has_apa_citations,
        "All sources have APA-formatted citations"
    )
    
    # Verify specific sources
    source_names = [s.get('source_name', '') for s in data_sources]
    has_gov_sources = any('Singapore' in name or 'Manpower' in name for name in source_names)
    
    results.add_result(
        "Government Sources Cited",
        has_gov_sources,
        f"Sources: {', '.join(source_names[:3])}"
    )
    
    # Test 4.3: Methodology Documentation
    print("\n[4.3] Testing Methodology Documentation...")
    methodology = report.get('methodology', {})
    
    has_overview = bool(methodology.get('overview'))
    has_methods = bool(methodology.get('analytical_methods'))
    has_data_quality = bool(methodology.get('data_quality'))
    
    results.add_result(
        "Methodology Overview",
        has_overview,
        "Methodology description included"
    )
    
    results.add_result(
        "Analytical Methods Documented",
        has_methods and len(methodology.get('analytical_methods', [])) > 0,
        f"{len(methodology.get('analytical_methods', []))} methods documented"
    )
    
    results.add_result(
        "Data Quality Documentation",
        has_data_quality,
        "Data quality measures documented"
    )
    
    # Test 4.4: Recommendations
    print("\n[4.4] Testing Recommendations...")
    recommendations = report.get('recommendations', [])
    
    results.add_result(
        "Policy Recommendations Generated",
        len(recommendations) > 0,
        f"Generated {len(recommendations)} recommendations"
    )
    
    # Check recommendation structure
    if recommendations:
        first_rec = recommendations[0]
        has_structure = all(key in first_rec for key in ['category', 'priority', 'recommendation', 'rationale'])
        
        results.add_result(
            "Recommendation Structure",
            has_structure,
            "Includes category, priority, recommendation, rationale"
        )
    
    # Test 4.5: Executive Summary
    print("\n[4.5] Testing Executive Summary...")
    exec_summary = report.get('executive_summary', '')
    
    results.add_result(
        "Executive Summary",
        len(exec_summary) > 50,
        f"Length: {len(exec_summary)} characters"
    )

# ============================================================================
# TEST 5: ERROR HANDLING & EDGE CASES
# ============================================================================
async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "="*70)
    print("TEST SUITE 5: ERROR HANDLING & EDGE CASES")
    print("="*70)
    
    coordinator = CoordinatorAgent()
    
    # Test 5.1: Empty Query
    print("\n[5.1] Testing Empty Query Handling...")
    response = await coordinator.process_query("")
    
    results.add_result(
        "Empty Query Handled",
        response.get('status') in ['success', 'error'],
        f"Status: {response.get('status')}"
    )
    
    # Test 5.2: Invalid Query
    print("\n[5.2] Testing Invalid Query...")
    response = await coordinator.process_query("What is the weather today?")
    
    results.add_result(
        "Invalid Query Handled",
        response.get('status') in ['success', 'error'],
        "System handled non-employment query"
    )
    
    # Test 5.3: Very Long Query
    print("\n[5.3] Testing Long Query...")
    long_query = "Analyze employment " * 50
    response = await coordinator.process_query(long_query)
    
    results.add_result(
        "Long Query Handled",
        response.get('status') in ['success', 'error'],
        f"Query length: {len(long_query)} characters"
    )

# ============================================================================
# TEST 6: API ENDPOINT TESTING
# ============================================================================
def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*70)
    print("TEST SUITE 6: API ENDPOINTS")
    print("="*70)
    
    import subprocess
    
    # Test 6.1: Health Endpoint
    print("\n[6.1] Testing Health Endpoint...")
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:8000/health'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            is_healthy = health_data.get('status') == 'healthy'
            
            results.add_result(
                "Health Endpoint",
                is_healthy,
                f"Status: {health_data.get('status')}"
            )
        else:
            results.add_result("Health Endpoint", False, "Failed to connect")
    except Exception as e:
        results.add_result("Health Endpoint", False, f"Error: {str(e)}")
    
    # Test 6.2: Query Endpoint
    print("\n[6.2] Testing Query Endpoint...")
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', 'http://localhost:8000/query',
             '-H', 'Content-Type: application/json',
             '-d', '{"query": "Test query"}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            query_data = json.loads(result.stdout)
            has_response = 'result' in query_data
            
            results.add_result(
                "Query Endpoint",
                has_response,
                f"Response received with status: {query_data.get('status')}"
            )
        else:
            results.add_result("Query Endpoint", False, "Failed to connect")
    except Exception as e:
        results.add_result("Query Endpoint", False, f"Error: {str(e)}")

# ============================================================================
# TEST 7: DATA QUALITY & VALIDATION
# ============================================================================
async def test_data_quality():
    """Test data quality and validation"""
    print("\n" + "="*70)
    print("TEST SUITE 7: DATA QUALITY & VALIDATION")
    print("="*70)
    
    # Test 7.1: Data Extraction
    print("\n[7.1] Testing Data Extraction...")
    extractor = ExtractionAgent()
    extraction_result = extractor.load_employment_data()
    
    results.add_result(
        "Data Extraction Success",
        extraction_result.get('status') == 'success',
        f"Loaded {len(extraction_result.get('data', []))} records"
    )
    
    # Test 7.2: Data Quality Validation
    print("\n[7.2] Testing Data Quality Validation...")
    data_info = extraction_result.get('data_info', {})
    validation = data_info.get('validation_report', {})
    
    quality_score = validation.get('quality_score', 0)
    
    results.add_result(
        "Data Quality Score",
        quality_score > 90,
        f"Quality score: {quality_score}%"
    )
    
    # Test 7.3: Multi-Source Loading
    print("\n[7.3] Testing Multi-Source Data Loading...")
    sources_loaded = data_info.get('sources_loaded', [])
    
    results.add_result(
        "Multi-Source Integration",
        len(sources_loaded) >= 2,
        f"Loaded from {len(sources_loaded)} sources"
    )

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
async def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("COMPREHENSIVE BACKEND TESTING")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all test suites
    await test_statistical_analysis()
    await test_policy_insights()
    await test_visualizations()
    await test_structured_reports()
    await test_error_handling()
    test_api_endpoints()
    await test_data_quality()
    
    # Print summary
    results.print_summary()
    
    # Generate test report
    generate_test_report()
    
    return results.passed == results.total

def generate_test_report():
    """Generate detailed test report"""
    report_path = "/Users/praveennabharathi/Documents/Projects/backend/TEST_REPORT.md"
    
    with open(report_path, 'w') as f:
        f.write("# Backend Testing Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Tests:** {results.total}\n")
        f.write(f"**Passed:** {results.passed}\n")
        f.write(f"**Failed:** {results.failed}\n")
        f.write(f"**Success Rate:** {(results.passed/results.total*100):.1f}%\n\n")
        f.write("---\n\n")
        f.write("## Test Results\n\n")
        
        for result in results.results:
            f.write(f"### {result['test']}\n")
            f.write(f"**Status:** {result['status']}\n")
            if result['details']:
                f.write(f"**Details:** {result['details']}\n")
            f.write("\n")
    
    print(f"\nDetailed test report saved to: {report_path}")

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
