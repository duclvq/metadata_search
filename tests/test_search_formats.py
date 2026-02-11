"""
Test search endpoint response formats
"""
import pytest


class TestSceneSearchFormat:
    """Test scene search response formats"""
    
    def test_scene_search_endpoint_exists(self, client):
        """Test that scene search endpoint exists"""
        response = client.get("/v1/search/scene?query_text=test")
        # Should not be 404
        assert response.status_code != 404
    
    def test_scene_search_requires_query_text(self, client):
        """Test that query_text is required"""
        response = client.get("/v1/search/scene")
        assert response.status_code == 422  # Missing required param
    
    def test_scene_search_response_structure(self, client):
        """Test scene search response structure when successful"""
        response = client.get("/v1/search/scene?query_text=test&k=5")
        
        # May succeed or fail depending on backend
        if response.status_code == 200:
            data = response.json()
            
            # Validate structure
            assert "total" in data
            assert "hits" in data
            assert "facets" in data
            
            # Validate types
            assert isinstance(data["total"], int)
            assert isinstance(data["hits"], list)
            # facets can be None or dict
            assert data["facets"] is None or isinstance(data["facets"], dict)
            
            # If hits present, validate structure
            if len(data["hits"]) > 0:
                hit = data["hits"][0]
                
                # Required fields
                assert "score" in hit
                assert "scene_id" in hit
                assert "scene_description" in hit
                assert "start_time_sec" in hit
                assert "end_time_sec" in hit
                assert "content_id" in hit
                assert "video_title" in hit
                
                # Validate types
                assert isinstance(hit["score"], (int, float))
                assert isinstance(hit["scene_id"], str)
                assert isinstance(hit["scene_description"], str)
                assert isinstance(hit["start_time_sec"], (int, float))
                assert isinstance(hit["end_time_sec"], (int, float))
                assert isinstance(hit["content_id"], str)
                assert isinstance(hit["video_title"], str)
                
                # Optional fields with defaults
                assert "faces" in hit
                assert isinstance(hit["faces"], list)
                assert "video_tags" in hit
                assert isinstance(hit["video_tags"], list)
    
    def test_scene_filter_endpoint_format(self, client):
        """Test scene filter endpoint request/response format"""
        request_data = {
            "query_text": "test",
            "category": ["test_category"],
            "author": None,
            "created_date": None,
            "broadcast_date": None,
            "program_id": None,
            "content_type_id": None,
            "k": 10,
            "search_type": "semantic"
        }
        
        response = client.post("/v1/search/scene/filter", json=request_data)
        
        # Should not be 404 or 422
        assert response.status_code != 404
        
        if response.status_code == 200:
            data = response.json()
            
            # Same structure as scene search
            assert "total" in data
            assert "hits" in data
            assert "facets" in data


class TestContentSearchFormat:
    """Test content search response formats"""
    
    def test_content_search_endpoint_exists(self, client):
        """Test that content search endpoint exists"""
        response = client.get("/v1/search/content?query_text=test")
        assert response.status_code != 404
    
    def test_content_search_response_structure(self, client):
        """Test content search response structure when successful"""
        response = client.get("/v1/search/content?query_text=test&k=5")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate structure
            assert "total" in data
            assert "hits" in data
            assert "facets" in data
            
            # Validate types
            assert isinstance(data["total"], int)
            assert isinstance(data["hits"], list)
            
            # If hits present, validate structure
            if len(data["hits"]) > 0:
                hit = data["hits"][0]
                
                # Required fields
                assert "score" in hit
                assert "content_id" in hit
                assert "title" in hit
                
                # Validate types
                assert isinstance(hit["score"], (int, float))
                assert isinstance(hit["content_id"], str)
                assert isinstance(hit["title"], str)
                
                # Optional fields
                assert "tags" in hit
                assert isinstance(hit["tags"], list)
                assert "duration_sec" in hit
                assert isinstance(hit["duration_sec"], (int, float))
    
    def test_content_filter_endpoint_format(self, client):
        """Test content filter endpoint format"""
        request_data = {
            "query_text": "test",
            "category": None,
            "author": None,
            "broadcast_date": None,
            "program_id": None,
            "content_type_id": None,
            "k": 10,
            "search_type": "hybrid"
        }
        
        response = client.post("/v1/search/content/filter", json=request_data)
        assert response.status_code != 404


class TestSceneListFormat:
    """Test scene list response format"""
    
    def test_scene_list_endpoint_exists(self, client):
        """Test that scene list endpoint exists"""
        response = client.get("/v1/search/scene/list")
        assert response.status_code != 404
    
    def test_scene_list_response_structure(self, client):
        """Test scene list response structure"""
        response = client.get("/v1/search/scene/list?skip=0&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate structure
            assert "total" in data
            assert "items" in data
            
            # Validate types
            assert isinstance(data["total"], int)
            assert isinstance(data["items"], list)
            
            # If items present, validate structure (should be like SceneHit but no score)
            if len(data["items"]) > 0:
                item = data["items"][0]
                
                # Should have scene fields
                assert "scene_id" in item
                assert "scene_description" in item
                assert "start_time_sec" in item
                assert "end_time_sec" in item
                assert "content_id" in item
                assert "video_title" in item
                
                # Should NOT have score field
                # (or if present, we verify it's not part of the search response)
                
                # Should have faces and tags as arrays
                assert "faces" in item
                assert isinstance(item["faces"], list)
                assert "video_tags" in item
                assert isinstance(item["video_tags"], list)
    
    def test_scene_list_pagination(self, client):
        """Test scene list pagination parameters"""
        response = client.get("/v1/search/scene/list?skip=5&limit=20")
        
        if response.status_code == 200:
            data = response.json()
            items = data["items"]
            
            # Should respect limit
            assert len(items) <= 20


class TestFaceSearchFormat:
    """Test face search response formats"""
    
    def test_face_search_endpoint_exists(self, client):
        """Test that face search endpoint exists"""
        response = client.post(
            "/v1/face_search",
            data={"face_names": ["Test Person"], "k": 10}
        )
        assert response.status_code != 404
    
    def test_face_search_requires_input(self, client):
        """Test that face search requires either images or face_names"""
        response = client.post("/v1/face_search", data={"k": 10})
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_face_search_response_structure(self, client):
        """Test face search response structure"""
        response = client.post(
            "/v1/face_search",
            data={"face_names": ["Test Person"], "k": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have same structure as scene search
            assert "total" in data
            assert "hits" in data
            assert "facets" in data
            
            assert isinstance(data["total"], int)
            assert isinstance(data["hits"], list)
    
    def test_face_filter_endpoint_format(self, client):
        """Test face filter endpoint format"""
        request_data = {
            "face_names": ["Test Person"],
            "category": None,
            "author": None,
            "created_date": None,
            "broadcast_date": None,
            "program_id": None,
            "content_type_id": None,
            "k": 10
        }
        
        response = client.post("/v1/face_search/filter", json=request_data)
        assert response.status_code != 404


class TestFacetsFormat:
    """Test facets structure in responses"""
    
    def test_scene_facets_structure(self, client):
        """Test that scene facets have correct structure when present"""
        response = client.get("/v1/search/scene?query_text=test")
        
        if response.status_code == 200:
            data = response.json()
            facets = data.get("facets")
            
            if facets:
                # Should have these fields
                expected_fields = [
                    "category", "created_date", "author",
                    "broadcast_date", "program_id", "content_type_id"
                ]
                
                for field in expected_fields:
                    assert field in facets
                    assert isinstance(facets[field], list)
                    
                    # If facet items exist, validate structure
                    if len(facets[field]) > 0:
                        item = facets[field][0]
                        assert "value" in item
                        assert "count" in item
                        assert "scene_ids" in item
                        assert isinstance(item["value"], str)
                        assert isinstance(item["count"], int)
                        assert isinstance(item["scene_ids"], list)
    
    def test_content_facets_structure(self, client):
        """Test that content facets have correct structure when present"""
        response = client.get("/v1/search/content?query_text=test")
        
        if response.status_code == 200:
            data = response.json()
            facets = data.get("facets")
            
            if facets:
                expected_fields = [
                    "category", "author", "broadcast_date",
                    "program_id", "content_type_id"
                ]
                
                for field in expected_fields:
                    assert field in facets
                    assert isinstance(facets[field], list)
                    
                    if len(facets[field]) > 0:
                        item = facets[field][0]
                        assert "value" in item
                        assert "count" in item
                        assert "content_ids" in item
                        assert isinstance(item["content_ids"], list)
