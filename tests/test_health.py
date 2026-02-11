"""
Test health check endpoint
"""


def test_health_check(client):
    """Test GET /health endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_response_format(client):
    """Validate health check response format"""
    response = client.get("/health")
    data = response.json()
    
    # Validate structure
    assert isinstance(data, dict)
    assert "status" in data
    assert data["status"] == "ok"
    
    # Validate types
    assert isinstance(data["status"], str)
