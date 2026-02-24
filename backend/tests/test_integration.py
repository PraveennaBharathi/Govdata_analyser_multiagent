"""
Integration tests for multi-agent workflows
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from agents.coordinator_agent import CoordinatorAgent
from agents.extraction.extraction_agent import ExtractionAgent
from agents.analytics.analytics_agent import AnalyticsAgent
from services.llm_service import LLMService


class TestMultiAgentWorkflow:
    """Integration tests for complete multi-agent workflows"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service"""
        mock = Mock()
        mock.generate_response = AsyncMock(return_value='{"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}')
        return mock
    
    @pytest.fixture
    def coordinator(self, mock_llm_service):
        """Create coordinator agent with mocked dependencies"""
        return CoordinatorAgent(llm_service=mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(self, coordinator):
        """Test complete query processing workflow"""
        query = "Analyze employment trends from 2020 to 2024"
        
        with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
            mock_extract.return_value = {
                "status": "success",
                "data": [
                    {'year': 2020, 'sector': 'Services', 'employment_count': 100000},
                    {'year': 2021, 'sector': 'Services', 'employment_count': 105000},
                ],
                "data_info": {
                    "sources_loaded": ["data.gov.sg"],
                    "total_records": 2
                }
            }
            
            result = await coordinator.process_query(query)
            
            assert isinstance(result, dict)
            assert "status" in result
            assert "result" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_query_parsing_to_extraction(self, coordinator):
        """Test query parsing flows correctly to data extraction"""
        query = "Show me employment data for 2022"
        
        with patch.object(coordinator.llm_service, 'parse_query') as mock_parse:
            mock_parse.return_value = {
                "dataset": "employment",
                "year_range": "2022",
                "analysis": "trend"
            }
            
            with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
                mock_extract.return_value = {
                    "status": "success",
                    "data": [],
                    "data_info": {}
                }
                
                result = await coordinator.process_query(query)
                
                # Verify parse_query was called
                mock_parse.assert_called_once_with(query)
                # Verify extraction was called
                mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extraction_to_analysis_flow(self, coordinator):
        """Test data flows from extraction to analysis"""
        query = "Analyze employment trends"
        
        sample_data = [
            {'year': 2020, 'sector': 'Services', 'employment_count': 100000},
            {'year': 2021, 'sector': 'Services', 'employment_count': 105000},
        ]
        
        with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
            mock_extract.return_value = {
                "status": "success",
                "data": sample_data,
                "data_info": {"sources_loaded": ["test"]}
            }
            
            with patch.object(coordinator.analytics_agent, 'analyze_employment_trends') as mock_analyze:
                mock_analyze.return_value = {
                    "status": "success",
                    "yearly_trends": [],
                    "summary_statistics": {},
                    "insights": [],
                    "conversational_response": "Test response"
                }
                
                result = await coordinator.process_query(query)
                
                # Verify analysis was called with extracted data
                mock_analyze.assert_called_once()
                call_args = mock_analyze.call_args[0][0]
                assert call_args == sample_data
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, coordinator):
        """Test error handling across agent boundaries"""
        query = "Test query"
        
        with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
            mock_extract.return_value = {
                "status": "error",
                "error": "Data source unavailable"
            }
            
            result = await coordinator.process_query(query)
            
            # Should handle error gracefully
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_unsupported_dataset_handling(self, coordinator):
        """Test handling of unsupported dataset requests"""
        query = "Show me GDP data"
        
        with patch.object(coordinator.llm_service, 'parse_query') as mock_parse:
            mock_parse.return_value = {
                "dataset": "gdp",
                "year_range": "2020-2024",
                "analysis": "trend"
            }
            
            result = await coordinator.process_query(query)
            
            assert isinstance(result, dict)
            # Should return informative response about unsupported dataset
    
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, coordinator):
        """Test agent state transitions through workflow"""
        query = "Analyze employment trends"
        
        with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
            mock_extract.return_value = {
                "status": "success",
                "data": [{'year': 2020, 'sector': 'Services', 'employment_count': 100000}],
                "data_info": {}
            }
            
            with patch.object(coordinator.analytics_agent, 'analyze_employment_trends') as mock_analyze:
                mock_analyze.return_value = {
                    "status": "success",
                    "conversational_response": "Test"
                }
                
                result = await coordinator.process_query(query)
                
                # Workflow should complete successfully
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, coordinator):
        """Test multiple workflows can execute concurrently"""
        queries = [
            "Analyze employment trends",
            "Show workforce statistics",
            "Compare sector employment"
        ]
        
        with patch.object(coordinator.extraction_agent, 'load_employment_data') as mock_extract:
            mock_extract.return_value = {
                "status": "success",
                "data": [],
                "data_info": {}
            }
            
            with patch.object(coordinator.analytics_agent, 'analyze_employment_trends') as mock_analyze:
                mock_analyze.return_value = {
                    "status": "success",
                    "conversational_response": "Test"
                }
                
                # Execute queries concurrently
                import asyncio
                results = await asyncio.gather(*[
                    coordinator.process_query(q) for q in queries
                ])
                
                assert len(results) == len(queries)
                assert all(isinstance(r, dict) for r in results)
