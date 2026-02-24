"""
Unit tests for Analytics Agent
"""
import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from agents.analytics.analytics_agent import AnalyticsAgent


class TestAnalyticsAgent:
    """Test suite for AnalyticsAgent"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service"""
        mock = Mock()
        mock.generate_response = AsyncMock(return_value="Test insight 1\nTest insight 2\nTest insight 3")
        return mock
    
    @pytest.fixture
    def agent(self, mock_llm_service):
        """Create analytics agent instance"""
        return AnalyticsAgent(llm_service=mock_llm_service)
    
    @pytest.fixture
    def sample_employment_data(self):
        """Create sample employment data"""
        return [
            {'year': 2020, 'sector': 'Services', 'employment_count': 100000},
            {'year': 2021, 'sector': 'Services', 'employment_count': 105000},
            {'year': 2022, 'sector': 'Services', 'employment_count': 110000},
            {'year': 2020, 'sector': 'Manufacturing', 'employment_count': 50000},
            {'year': 2021, 'sector': 'Manufacturing', 'employment_count': 52000},
            {'year': 2022, 'sector': 'Manufacturing', 'employment_count': 54000},
        ]
    
    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.llm_service is not None
        assert hasattr(agent, 'report_generator')
    
    @pytest.mark.asyncio
    async def test_analyze_employment_trends(self, agent, sample_employment_data):
        """Test employment trend analysis"""
        result = await agent.analyze_employment_trends(sample_employment_data)
        
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "yearly_trends" in result
        assert "sector_trends" in result
        assert "summary_statistics" in result
        assert "insights" in result
        assert "conversational_response" in result
    
    @pytest.mark.asyncio
    async def test_calculate_yearly_trends(self, agent, sample_employment_data):
        """Test yearly trend calculation"""
        df = pd.DataFrame(sample_employment_data)
        trends = agent._calculate_yearly_trends(df)
        
        assert isinstance(trends, pd.DataFrame)
        assert 'year' in trends.columns
        assert 'employment_count' in trends.columns
        assert 'growth_rate' in trends.columns
        assert len(trends) == 3  # 2020, 2021, 2022
    
    @pytest.mark.asyncio
    async def test_calculate_sector_trends(self, agent, sample_employment_data):
        """Test sector trend calculation"""
        df = pd.DataFrame(sample_employment_data)
        sector_trends = agent._calculate_sector_trends(df)
        
        assert isinstance(sector_trends, list)
        assert len(sector_trends) > 0
        
        for trend in sector_trends:
            assert 'sector' in trend
            assert 'year' in trend
            assert 'employment_count' in trend
    
    @pytest.mark.asyncio
    async def test_calculate_summary_statistics(self, agent, sample_employment_data):
        """Test summary statistics calculation"""
        df = pd.DataFrame(sample_employment_data)
        yearly_trends = agent._calculate_yearly_trends(df)
        stats = agent._calculate_summary_statistics(df, yearly_trends)
        
        assert isinstance(stats, dict)
        assert 'total_employment' in stats
        assert 'avg_annual_growth' in stats
        assert 'total_years' in stats
        assert 'sectors_analyzed' in stats
    
    @pytest.mark.asyncio
    async def test_generate_insights_with_llm(self, agent, sample_employment_data):
        """Test insight generation using LLM"""
        df = pd.DataFrame(sample_employment_data)
        yearly_trends = agent._calculate_yearly_trends(df)
        
        insights = await agent._generate_insights(df, yearly_trends)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)
    
    @pytest.mark.asyncio
    async def test_generate_insights_fallback(self, agent, sample_employment_data):
        """Test insight generation fallback when LLM fails"""
        # Mock LLM to return None
        agent.llm_service.generate_response = AsyncMock(return_value=None)
        
        df = pd.DataFrame(sample_employment_data)
        yearly_trends = agent._calculate_yearly_trends(df)
        
        insights = await agent._generate_insights(df, yearly_trends)
        
        assert isinstance(insights, list)
        assert len(insights) > 0  # Should have fallback insights
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self, agent):
        """Test handling of empty data"""
        result = await agent.analyze_employment_trends([])
        
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_invalid_data_handling(self, agent):
        """Test handling of invalid data"""
        invalid_data = [
            {'year': 'invalid', 'sector': 'Services', 'employment_count': 'not_a_number'}
        ]
        
        result = await agent.analyze_employment_trends(invalid_data)
        
        assert isinstance(result, dict)
        # Should handle gracefully
    
    @pytest.mark.asyncio
    async def test_growth_rate_calculation(self, agent, sample_employment_data):
        """Test growth rate calculation accuracy"""
        df = pd.DataFrame(sample_employment_data)
        trends = agent._calculate_yearly_trends(df)
        
        # Check growth rate calculation
        for i in range(1, len(trends)):
            prev_count = trends.iloc[i-1]['employment_count']
            curr_count = trends.iloc[i]['employment_count']
            expected_growth = ((curr_count - prev_count) / prev_count) * 100
            
            assert abs(trends.iloc[i]['growth_rate'] - expected_growth) < 0.01
