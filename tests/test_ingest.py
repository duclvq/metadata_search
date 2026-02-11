"""
Test ingest endpoints
"""
import pytest


class TestSceneIngest:
    """Test scene ingest endpoint"""
    
    def test_scene_ingest_endpoint_exists(self, client):
        """Test that scene ingest endpoint exists"""
        # POST with empty data should fail validation
        response = client.post("/v1/scenes/ingest", json={})
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_scene_ingest_empty_scenes_fails(self, client):
        """Test scene ingest with empty scenes array fails"""
        response = client.post("/v1/scenes/ingest", json={"scenes": []})
        assert response.status_code == 422  # Validation error
    
    def test_scene_ingest_valid_format(self, client, sample_scene_data):
        """Test scene ingest with valid data format"""
        response = client.post("/v1/scenes/ingest", json=sample_scene_data)
        
        # May succeed or fail depending on backend availability
        # But should return proper response format
        assert response.status_code in [200, 502]
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            assert "indexed" in data
            assert "errors" in data
            
            # Validate types
            assert isinstance(data["indexed"], int)
            assert isinstance(data["errors"], list)
            
            # Validate indexed count is non-negative
            assert data["indexed"] >= 0
    
    def test_scene_ingest_missing_required_fields(self, client):
        """Test scene ingest with missing required fields"""
        invalid_data = {
            "scenes": [
                {
                    "scene_id": "test_001",
                    # Missing scene_description, start_time_sec, end_time_sec, video
                }
            ]
        }
        
        response = client.post("/v1/scenes/ingest", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_scene_ingest_response_format_on_error(self, client):
        """Test that error responses have proper format"""
        invalid_data = {"scenes": "not_an_array"}
        
        response = client.post("/v1/scenes/ingest", json=invalid_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data


class TestContentIngest:
    """Test content ingest endpoint"""
    
    def test_content_ingest_endpoint_exists(self, client):
        """Test that content ingest endpoint exists"""
        response = client.post("/v1/contents/ingest", json={})
        # Should not be 404
        assert response.status_code != 404
    
    def test_content_ingest_empty_contents_fails(self, client):
        """Test content ingest with empty contents array fails"""
        response = client.post("/v1/contents/ingest", json={"contents": []})
        assert response.status_code == 422
    
    def test_content_ingest_valid_format(self, client, sample_content_data):
        """Test content ingest with valid data format"""
        response = client.post("/v1/contents/ingest", json=sample_content_data)
        
        # May succeed (200), fail due to backend (502), or not implemented (501)
        assert response.status_code in [200, 501, 502]
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            assert "indexed" in data
            assert "errors" in data
            
            # Validate types
            assert isinstance(data["indexed"], int)
            assert isinstance(data["errors"], list)
            
            assert data["indexed"] >= 0
    
    def test_content_ingest_missing_required_fields(self, client):
        """Test content ingest with missing required fields"""
        invalid_data = {
            "contents": [
                {
                    "content_id": "test_001",
                    # Missing title
                }
            ]
        }
        
        response = client.post("/v1/contents/ingest", json=invalid_data)
        assert response.status_code == 422
    
    def test_content_ingest_invalid_types(self, client):
        """Test content ingest with invalid field types"""
        invalid_data = {
            "contents": [
                {
                    "content_id": "test_001",
                    "title": "Test",
                    "duration_sec": "not_a_number",  # Should be float
                    "tags": "not_an_array"  # Should be array
                }
            ]
        }
        
        response = client.post("/v1/contents/ingest", json=invalid_data)
        assert response.status_code == 422


class TestIngestDataValidation:
    """Test data validation for ingest endpoints"""
    
    def test_scene_ingest_validates_face_structure(self, client):
        """Test that face data structure is validated"""
        data = {
            "scenes": [
                {
                    "scene_id": "test_001",
                    "scene_description": "Test",
                    "start_time_sec": 0.0,
                    "end_time_sec": 10.0,
                    "faces": [
                        {"face_id": "f001"}  # Missing 'name'
                    ],
                    "video": {
                        "video_id": "v001",
                        "video_title": "Test"
                    }
                }
            ]
        }
        
        response = client.post("/v1/scenes/ingest", json=data)
        assert response.status_code == 422
    
    def test_scene_ingest_validates_video_structure(self, client):
        """Test that video data structure is validated"""
        data = {
            "scenes": [
                {
                    "scene_id": "test_001",
                    "scene_description": "Test",
                    "start_time_sec": 0.0,
                    "end_time_sec": 10.0,
                    "video": {
                        "video_id": "v001"
                        # Missing video_title
                    }
                }
            ]
        }
        
        response = client.post("/v1/scenes/ingest", json=data)
        assert response.status_code == 422
    
    def test_scene_ingest_validates_time_ranges(self, client):
        """Test that time ranges are validated as numbers"""
        data = {
            "scenes": [
                {
                    "scene_id": "test_001",
                    "scene_description": "Test",
                    "start_time_sec": "invalid",  # Should be float
                    "end_time_sec": 10.0,
                    "video": {
                        "video_id": "v001",
                        "video_title": "Test"
                    }
                }
            ]
        }
        
        response = client.post("/v1/scenes/ingest", json=data)
        assert response.status_code == 422
    
    def test_content_ingest_validates_tags_as_array(self, client):
        """Test that tags must be an array"""
        data = {
            "contents": [
                {
                    "content_id": "c001",
                    "title": "Test",
                    "tags": {"not": "an_array"}  # Should be array
                }
            ]
        }
        
        response = client.post("/v1/contents/ingest", json=data)
        assert response.status_code == 422
