#!/usr/bin/env python3
"""
Comprehensive test script for all agents and their processes
"""
import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coordinator_agent import CoordinatorAgent
from agents.extraction.extraction_agent import ExtractionAgent
from agents.analytics.analytics_agent import AnalyticsAgent
from services.llm_service import LLMService

async def test_llm_service():
    """Test LLM service with fallback mechanism"""
    print("\n" + "="*60)
    print("TEST 1: LLM Service")
    print("="*60)
    
    llm = LLMService()
    
    # Check which clients are initialized
    print(f"✓ Gemini client: {'Initialized' if llm.gemini_client else 'Not available'}")
    print(f"✓ Mistral client: {'Initialized' if llm.mistral_client else 'Not available'}")
    print(f"✓ OpenAI client: {'Initialized' if llm.openai_client else 'Not available'}")
    
    # Test query parsing
    try:
        result = await llm.parse_query("Show me employment trends from 2020 to 2024")
        print(f"✓ Query parsing successful: {result}")
        return True
    except Exception as e:
        print(f"✗ Query parsing failed: {e}")
        return False

def test_extraction_agent():
    """Test Extraction Agent data loading"""
    print("\n" + "="*60)
    print("TEST 2: Extraction Agent")
    print("="*60)
    
    extractor = ExtractionAgent()
    
    # Test data loading
    result = extractor.load_employment_data()
    
    if result["status"] == "success":
        print(f"✓ Data extraction successful")
        print(f"  - Sources loaded: {result['data_info']['sources_loaded']}")
        print(f"  - Total records: {result['data_info']['total_records']}")
        print(f"  - Years covered: {result['data_info']['years_covered']}")
        print(f"  - Sectors: {len(result['data_info']['sectors'])} sectors")
        print(f"  - Quality score: {result['data_info']['validation_report']['quality_score']}%")
        
        # Check validation report
        validation = result['data_info']['validation_report']
        print(f"\n  Data Quality Metrics:")
        print(f"  - Duplicate records: {validation['duplicate_records']}")
        print(f"  - Missing values: {len(validation['missing_values'])} columns")
        print(f"  - Outliers detected: {len(validation['outliers'])} columns")
        
        return True
    else:
        print(f"✗ Data extraction failed: {result.get('error')}")
        return False

async def test_analytics_agent():
    """Test Analytics Agent trend analysis"""
    print("\n" + "="*60)
    print("TEST 3: Analytics Agent")
    print("="*60)
    
    # First get data
    extractor = ExtractionAgent()
    data_result = extractor.load_employment_data()
    
    if data_result["status"] != "success":
        print("✗ Cannot test analytics - data extraction failed")
        return False
    
    # Test analytics
    analytics = AnalyticsAgent()
    result = await analytics.analyze_employment_trends(data_result["data"])
    
    if result["status"] == "success":
        print(f"✓ Analytics successful")
        print(f"  - Yearly trends: {len(result['yearly_trends'])} years analyzed")
        print(f"  - Sector trends: {len(result['sector_trends'])} sector-year combinations")
        print(f"  - Insights generated: {len(result['insights'])} insights")
        print(f"  - Chart generated: {'Yes' if result['chart'] else 'No (matplotlib not available)'}")
        
        # Show summary statistics
        stats = result['summary_statistics']
        print(f"\n  Summary Statistics:")
        print(f"  - Total years: {stats['total_years']}")
        print(f"  - Avg annual growth: {stats['avg_annual_growth']:.2f}%")
        print(f"  - Max employment: {stats['max_employment']:,.0f}")
        print(f"  - Min employment: {stats['min_employment']:,.0f}")
        
        return True
    else:
        print(f"✗ Analytics failed: {result.get('error')}")
        return False

async def test_coordinator_agent():
    """Test Coordinator Agent workflow orchestration"""
    print("\n" + "="*60)
    print("TEST 4: Coordinator Agent (Full Workflow)")
    print("="*60)
    
    coordinator = CoordinatorAgent()
    
    # Test full workflow
    result = await coordinator.process_query("Analyze employment trends from 2020 to 2024")
    
    if result["status"] == "success":
        print(f"✓ Coordinator workflow successful")
        print(f"  - Parsed query: {result['parsed_query']}")
        print(f"  - Analysis plan steps: {len(result['analysis_plan'])}")
        print(f"  - Workflow steps executed: {len(result['workflow_steps'])}")
        print(f"  - Final status: {result['result']['status']}")
        
        # Show workflow steps
        print(f"\n  Workflow Steps:")
        for i, step in enumerate(result['workflow_steps'], 1):
            print(f"    {i}. {step}")
        
        # Show extraction summary
        extraction = result['result']['extraction_summary']
        print(f"\n  Extraction Summary:")
        print(f"    - Status: {extraction['status']}")
        print(f"    - Records: {extraction['records_count']}")
        
        # Show analysis summary
        analysis = result['result']['analysis']
        if analysis['status'] == 'success':
            print(f"\n  Analysis Summary:")
            print(f"    - Years analyzed: {len(analysis['yearly_trends'])}")
            print(f"    - Avg growth: {analysis['summary_statistics']['avg_annual_growth']:.2f}%")
        
        return True
    else:
        print(f"✗ Coordinator workflow failed: {result.get('error')}")
        return False

async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "="*60)
    print("TEST 5: Error Handling")
    print("="*60)
    
    coordinator = CoordinatorAgent()
    
    # Test with empty query
    result1 = await coordinator.process_query("")
    print(f"✓ Empty query handled: {result1['status']}")
    
    # Test with unusual query
    result2 = await coordinator.process_query("What is the weather today?")
    print(f"✓ Unusual query handled: {result2['status']}")
    
    return True

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AGENTIC POLICY DATA ANALYTICS PLATFORM")
    print("Agent Process Verification Tests")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("LLM Service", await test_llm_service()))
    results.append(("Extraction Agent", test_extraction_agent()))
    results.append(("Analytics Agent", await test_analytics_agent()))
    results.append(("Coordinator Agent", await test_coordinator_agent()))
    results.append(("Error Handling", await test_error_handling()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    print("="*60)
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
