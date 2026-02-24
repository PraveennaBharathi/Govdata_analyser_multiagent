"""
Unit tests for Extraction Agent
"""
import pytest
import pandas as pd
from pathlib import Path
from agents.extraction.extraction_agent import ExtractionAgent


class TestExtractionAgent:
    """Test suite for ExtractionAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create extraction agent instance"""
        return ExtractionAgent(data_dir="data")
    
    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.data_dir == Path("data")
        assert isinstance(agent.data_sources, dict)
        assert len(agent.data_sources) > 0
        assert agent.data_cache == {}
        assert agent.validation_errors == []
    
    def test_load_employment_data_structure(self, agent):
        """Test employment data loading returns correct structure"""
        result = agent.load_employment_data()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["success", "error"]
        
        if result["status"] == "success":
            assert "data_info" in result
            assert "data" in result
            assert isinstance(result["data"], list)
    
    def test_data_validation(self, agent):
        """Test data quality validation"""
        # Create sample data
        sample_data = pd.DataFrame({
            'year': [2020, 2021, 2022],
            'sector': ['Services', 'Manufacturing', 'Construction'],
            'employment_count': [100000, 95000, 105000]
        })
        
        validation_report = agent._validate_data_quality(sample_data)
        
        assert isinstance(validation_report, dict)
        assert "quality_score" in validation_report
        assert "issues" in validation_report
        assert 0 <= validation_report["quality_score"] <= 100
    
    def test_data_cleaning(self, agent):
        """Test data cleaning removes duplicates and handles missing values"""
        # Create sample data with duplicates and missing values
        sample_data = pd.DataFrame({
            'year': [2020, 2020, 2021, 2022, None],
            'sector': ['Services', 'Services', 'Manufacturing', None, 'Construction'],
            'employment_count': [100000, 100000, 95000, 105000, 90000]
        })
        
        cleaned = agent._clean_data(sample_data)
        
        assert isinstance(cleaned, pd.DataFrame)
        assert len(cleaned) < len(sample_data)  # Duplicates removed
        assert cleaned['year'].notna().all()  # No missing years
    
    def test_csv_loading_error_handling(self, agent):
        """Test CSV loading handles missing files gracefully"""
        result = agent._load_csv_data("nonexistent_file.csv", "test_source")
        
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "error" in result
    
    def test_data_cache(self, agent):
        """Test data caching mechanism"""
        result = agent.load_employment_data()
        
        if result["status"] == "success":
            assert "employment" in agent.data_cache
            assert isinstance(agent.data_cache["employment"], pd.DataFrame)
    
    def test_data_sources_configuration(self, agent):
        """Test data sources are properly configured"""
        assert "data.gov.sg" in agent.data_sources
        assert "MOM Statistics" in agent.data_sources
        assert "DOS SingStat" in agent.data_sources
        
        for source, filename in agent.data_sources.items():
            assert isinstance(filename, str)
            assert len(filename) > 0
