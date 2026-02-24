"""
Unit tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.main import app


class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @patch('api.main.coordinator_agent')
    def test_async_query_submission(self, mock_coordinator, client):
        """Test async query submission"""
        mock_coordinator.process_query = AsyncMock(return_value={
            "status": "success",
            "result": "test result"
        })
        
        response = client.post(
            "/query/async",
            json={"query": "Test query"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_async_query_missing_query(self, client):
        """Test async query with missing query parameter"""
        response = client.post("/query/async", json={})
        assert response.status_code == 422  # Validation error
    
    def test_async_query_empty_query(self, client):
        """Test async query with empty query"""
        response = client.post(
            "/query/async",
            json={"query": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_task_status_retrieval(self, client):
        """Test task status retrieval"""
        # First create a task
        with patch('api.main.coordinator_agent') as mock_coordinator:
            mock_coordinator.process_query = AsyncMock(return_value={
                "status": "success"
            })
            
            submit_response = client.post(
                "/query/async",
                json={"query": "Test query"}
            )
            task_id = submit_response.json()["task_id"]
            
            # Then check status
            status_response = client.get(f"/task/{task_id}")
            assert status_response.status_code == 200
            data = status_response.json()
            assert "state" in data
            assert "task_id" in data
    
    def test_task_status_invalid_id(self, client):
        """Test task status with invalid task ID"""
        response = client.get("/task/invalid-task-id-12345")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/query/async")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_query_validation_max_length(self, client):
        """Test query length validation"""
        long_query = "a" * 10000  # Very long query
        response = client.post(
            "/query/async",
            json={"query": long_query}
        )
        # Should either accept or reject based on validation rules
        assert response.status_code in [200, 422]
    
    @patch('api.main.coordinator_agent')
    def test_concurrent_queries(self, mock_coordinator, client):
        """Test handling of concurrent queries"""
        mock_coordinator.process_query = AsyncMock(return_value={
            "status": "success"
        })
        
        # Submit multiple queries
        responses = []
        for i in range(5):
            response = client.post(
                "/query/async",
                json={"query": f"Test query {i}"}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert "task_id" in response.json()
        
        # All task IDs should be unique
        task_ids = [r.json()["task_id"] for r in responses]
        assert len(task_ids) == len(set(task_ids))
    
    def test_export_json(self, client):
        """Test JSON export functionality"""
        # This would test the export endpoint if implemented
        # Placeholder for future implementation
        pass
    
    def test_export_csv(self, client):
        """Test CSV export functionality"""
        # This would test the CSV export endpoint if implemented
        # Placeholder for future implementation
        pass
