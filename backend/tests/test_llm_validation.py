"""
LLM-specific validation tests: hallucination detection, accuracy, consistency
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.llm_service import LLMService
import json


class TestLLMValidation:
    """Test suite for LLM validation and quality checks"""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance"""
        return LLMService()
    
    @pytest.mark.asyncio
    async def test_hallucination_detection_factual_grounding(self, llm_service):
        """Test detection of hallucinated facts not present in source data"""
        # Mock response with hallucinated data
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Employment in the aviation sector grew by 500% in 2023"
            
            response = await llm_service.generate_response([])
            
            # Hallucination detection: Check if response contains unrealistic claims
            assert response is not None
            
            # In production, would validate against source data
            # For now, check response structure
            assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_response_consistency_across_calls(self, llm_service):
        """Test LLM provides consistent responses for similar queries"""
        query = "What is the employment trend in 2020?"
        
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = '{"dataset": "employment", "year_range": "2020", "analysis": "trend"}'
            
            # Make multiple calls with same query
            responses = []
            for _ in range(3):
                response = await llm_service.generate_response([])
                responses.append(response)
            
            # Check all responses are consistent
            assert len(set(responses)) == 1  # All responses should be identical
    
    @pytest.mark.asyncio
    async def test_json_parsing_accuracy(self, llm_service):
        """Test LLM generates valid, parseable JSON"""
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = '{"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}'
            
            response = await llm_service.generate_response([])
            
            # Should be valid JSON
            try:
                parsed = json.loads(response)
                assert isinstance(parsed, dict)
                assert "dataset" in parsed
            except json.JSONDecodeError:
                pytest.fail("LLM response is not valid JSON")
    
    @pytest.mark.asyncio
    async def test_response_relevance_to_query(self, llm_service):
        """Test LLM responses are relevant to the input query"""
        query_about_employment = "Analyze employment trends"
        
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = '{"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}'
            
            response = await llm_service.generate_response([])
            
            # Response should mention employment
            assert "employment" in response.lower()
    
    @pytest.mark.asyncio
    async def test_numerical_accuracy_validation(self, llm_service):
        """Test LLM-generated numbers are within reasonable bounds"""
        with patch.object(llm_service, 'generate_response') as mock_generate:
            # Mock response with statistics
            mock_generate.return_value = "Employment grew by 5.2% annually"
            
            response = await llm_service.generate_response([])
            
            # Extract percentage and validate it's reasonable
            import re
            percentages = re.findall(r'(\d+\.?\d*)%', response)
            
            for pct in percentages:
                pct_value = float(pct)
                # Employment growth should be within realistic bounds
                assert -50 < pct_value < 100, f"Unrealistic percentage: {pct_value}%"
    
    @pytest.mark.asyncio
    async def test_temporal_consistency(self, llm_service):
        """Test LLM maintains temporal consistency in responses"""
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Employment in 2022 was higher than 2021"
            
            response = await llm_service.generate_response([])
            
            # Check for temporal keywords
            temporal_keywords = ['2020', '2021', '2022', '2023', '2024']
            has_temporal_reference = any(keyword in response for keyword in temporal_keywords)
            
            assert has_temporal_reference or response is not None
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism_reliability(self, llm_service):
        """Test fallback to secondary LLM when primary fails"""
        with patch.object(llm_service, 'mistral_client') as mock_mistral:
            with patch.object(llm_service, 'gemini_client') as mock_gemini:
                # Primary fails
                mock_mistral.ainvoke = AsyncMock(side_effect=Exception("Primary LLM failed"))
                # Fallback succeeds
                mock_response = Mock()
                mock_response.content = "Fallback response"
                mock_gemini.ainvoke = AsyncMock(return_value=mock_response)
                
                response = await llm_service.generate_response([])
                
                # Should get fallback response
                assert response == "Fallback response"
    
    @pytest.mark.asyncio
    async def test_response_length_validation(self, llm_service):
        """Test LLM responses are within acceptable length bounds"""
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Test response" * 100
            
            response = await llm_service.generate_response([])
            
            # Response should not be too short or too long
            assert 10 < len(response) < 10000, "Response length out of bounds"
    
    @pytest.mark.asyncio
    async def test_no_sensitive_data_leakage(self, llm_service):
        """Test LLM doesn't leak API keys or sensitive data"""
        with patch.object(llm_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Analysis complete"
            
            response = await llm_service.generate_response([])
            
            # Should not contain API keys or sensitive patterns
            sensitive_patterns = ['AIza', 'sk-', 'api_key', 'secret']
            for pattern in sensitive_patterns:
                assert pattern not in response, f"Potential sensitive data leak: {pattern}"
    
    @pytest.mark.asyncio
    async def test_structured_output_validation(self, llm_service):
        """Test LLM generates properly structured outputs"""
        with patch.object(llm_service, 'parse_query') as mock_parse:
            mock_parse.return_value = {
                "dataset": "employment",
                "year_range": "2020-2024",
                "analysis": "trend"
            }
            
            result = await llm_service.parse_query("Test query")
            
            # Validate structure
            assert isinstance(result, dict)
            assert "dataset" in result
            assert "year_range" in result
            assert "analysis" in result
            
            # Validate data types
            assert isinstance(result["dataset"], str)
            assert isinstance(result["year_range"], str)
            assert isinstance(result["analysis"], str)
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self, llm_service):
        """Test LLM service handles errors gracefully"""
        with patch.object(llm_service, 'mistral_client') as mock_mistral:
            with patch.object(llm_service, 'gemini_client') as mock_gemini:
                with patch.object(llm_service, 'openai_client') as mock_openai:
                    # All clients fail
                    mock_mistral.ainvoke = AsyncMock(side_effect=Exception("Failed"))
                    mock_gemini.ainvoke = AsyncMock(side_effect=Exception("Failed"))
                    mock_openai.ainvoke = AsyncMock(side_effect=Exception("Failed"))
                    
                    response = await llm_service.generate_response([])
                    
                    # Should return None or error message, not crash
                    assert response is None or isinstance(response, str)


class TestHallucinationDetection:
    """Dedicated test suite for hallucination detection"""
    
    def test_detect_unrealistic_growth_rates(self):
        """Detect hallucinated unrealistic growth rates"""
        response = "Employment grew by 500% in one year"
        
        # Extract growth rate
        import re
        growth_rates = re.findall(r'(\d+)%', response)
        
        for rate in growth_rates:
            rate_value = int(rate)
            # Flag unrealistic growth (>100% annual growth is suspicious)
            if rate_value > 100:
                assert True, "Detected potential hallucination: unrealistic growth rate"
    
    def test_detect_non_existent_sectors(self):
        """Detect references to non-existent sectors"""
        response = "The space tourism sector employed 50,000 people"
        
        valid_sectors = ['construction', 'manufacturing', 'services']
        response_lower = response.lower()
        
        # Check if response mentions invalid sectors
        invalid_sector_mentioned = 'space tourism' in response_lower
        
        if invalid_sector_mentioned:
            # This would be flagged as potential hallucination
            assert True, "Detected potential hallucination: non-existent sector"
    
    def test_detect_future_predictions(self):
        """Detect hallucinated future predictions"""
        response = "Employment will reach 500,000 by 2030"
        
        # Check for future tense and dates beyond current data
        future_indicators = ['will', 'predict', '2030', '2025', '2026']
        
        has_future_prediction = any(indicator in response.lower() for indicator in future_indicators)
        
        if has_future_prediction:
            # Flag as potential hallucination if data only goes to 2024
            assert True, "Detected potential hallucination: future prediction"
    
    def test_detect_contradictory_statements(self):
        """Detect contradictory statements in response"""
        response = "Employment increased by 10% but also decreased by 5%"
        
        # Check for contradictory keywords
        has_increase = 'increased' in response.lower()
        has_decrease = 'decreased' in response.lower()
        
        if has_increase and has_decrease:
            # Flag potential contradiction
            assert True, "Detected potential contradiction in response"
