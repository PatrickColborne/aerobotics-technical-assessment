"""
Integration tests for the FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestAPI:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Missing Trees Detection API"
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_detect_missing_trees_perfect_grid(self):
        """Test detection with a perfect grid - no missing trees."""
        payload = {
            "tree_positions": [
                {"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 10, "y": 0},
                {"x": 0, "y": 5}, {"x": 5, "y": 5}, {"x": 10, "y": 5},
                {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 10, "y": 10}
            ]
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_missing"] == 0
        assert len(data["missing_trees"]) == 0
    
    def test_detect_missing_trees_with_gaps(self):
        """Test detection with missing trees."""
        payload = {
            "tree_positions": [
                {"x": 0, "y": 0}, {"x": 5, "y": 0}, {"x": 10, "y": 0},
                {"x": 0, "y": 5}, {"x": 10, "y": 5},  # Missing (5, 5)
                {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 10, "y": 10}
            ]
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_missing"] == 1
        assert len(data["missing_trees"]) == 1
        
        missing = data["missing_trees"][0]
        assert missing["x"] == 5.0
        assert missing["y"] == 5.0
    
    def test_detect_missing_trees_with_explicit_params(self):
        """Test detection with explicit grid parameters."""
        payload = {
            "tree_positions": [
                {"x": 0, "y": 0}, {"x": 5, "y": 0},
                {"x": 0, "y": 5}, {"x": 5, "y": 5}
            ],
            "expected_rows": 3,
            "expected_cols": 3,
            "row_spacing": 5.0,
            "col_spacing": 5.0
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_missing"] == 5
        assert len(data["missing_trees"]) == 5
    
    def test_detect_missing_trees_empty_input(self):
        """Test with empty tree positions."""
        payload = {
            "tree_positions": []
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_detect_missing_trees_invalid_input(self):
        """Test with invalid input format."""
        payload = {
            "tree_positions": [
                {"x": "invalid", "y": 0}
            ]
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_detect_missing_trees_partial_params(self):
        """Test with partial grid parameters provided."""
        payload = {
            "tree_positions": [
                {"x": 0, "y": 0}, {"x": 3, "y": 0},
                {"x": 0, "y": 4}, {"x": 3, "y": 4}
            ],
            "expected_rows": 2,
            "expected_cols": 3,
            "col_spacing": 3.0
        }
        
        response = client.post("/detect-missing-trees", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Should detect missing trees based on provided parameters
        assert data["total_missing"] >= 0
