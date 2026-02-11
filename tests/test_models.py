"""
Test response model validation - validate format definitions
"""
import pytest
from pydantic import ValidationError

from api.models.search import (
    SceneHit,
    FaceItem,
    Facets,
    FacetItem,
    SearchResponse,
    ContentHit,
    ContentFacets,
    ContentFacetItem,
    ContentSearchResponse,
)
from api.models.scene import (
    FaceInfo,
    VideoInfo,
    SceneIngestItem,
    IngestRequest,
    ContentIngestItem,
    ContentIngestRequest,
    IngestResponse,
)


class TestSceneModels:
    """Test Scene-related models"""
    
    def test_face_item_valid(self):
        """Test FaceItem with valid data"""
        face = FaceItem(face_id="f001", name="Nguyen Van A")
        assert face.face_id == "f001"
        assert face.name == "Nguyen Van A"
    
    def test_scene_hit_valid(self):
        """Test SceneHit with valid data"""
        scene = SceneHit(
            score=0.856,
            scene_id="video123_scene_001",
            scene_description="Test scene",
            visual_caption="Test caption",
            audio_summarization="Test summary",
            audio_transcription="Test transcript",
            faces=[FaceItem(face_id="f001", name="Test Person")],
            start_time_sec=125.5,
            end_time_sec=148.2,
            content_id="video123",
            video_title="Test Video",
            video_name="test.mp4",
            video_summary="Test summary",
            video_tags=["test"],
            video_duration_sec=3600.0,
            video_created_at="2026-01-15T10:30:00",
            resolution="1920x1080",
            fps=30.0,
            program_id="prog_001",
            broadcast_date="2026-01-20",
            content_type_id="test_type",
            category="business",
            created_date="2026-01-15",
            author="Test Author"
        )
        
        assert scene.score == 0.856
        assert scene.scene_id == "video123_scene_001"
        assert len(scene.faces) == 1
        assert scene.faces[0].name == "Test Person"
    
    def test_scene_hit_optional_fields(self):
        """Test SceneHit with minimal required fields"""
        scene = SceneHit(
            score=1.0,
            scene_id="test_scene",
            scene_description="Test",
            start_time_sec=0.0,
            end_time_sec=10.0,
            content_id="test_video",
            video_title="Test"
        )
        
        assert scene.visual_caption == ""
        assert scene.audio_summarization == ""
        assert scene.audio_transcription == ""
        assert scene.faces == []
        assert scene.video_tags == []
    
    def test_facet_item_valid(self):
        """Test FacetItem with valid data"""
        facet = FacetItem(
            value="business",
            count=25,
            scene_ids=["scene001", "scene002"]
        )
        
        assert facet.value == "business"
        assert facet.count == 25
        assert len(facet.scene_ids) == 2
    
    def test_facets_valid(self):
        """Test Facets with valid data"""
        facets = Facets(
            category=[
                FacetItem(value="business", count=10, scene_ids=["s1"])
            ],
            created_date=[],
            author=[],
            broadcast_date=[],
            program_id=[],
            content_type_id=[]
        )
        
        assert len(facets.category) == 1
        assert facets.category[0].value == "business"
    
    def test_search_response_valid(self):
        """Test SearchResponse with valid data"""
        response = SearchResponse(
            total=42,
            hits=[
                SceneHit(
                    score=0.9,
                    scene_id="s1",
                    scene_description="Test",
                    start_time_sec=0.0,
                    end_time_sec=10.0,
                    content_id="v1",
                    video_title="Test"
                )
            ],
            facets=Facets(
                category=[], created_date=[], author=[],
                broadcast_date=[], program_id=[], content_type_id=[]
            )
        )
        
        assert response.total == 42
        assert len(response.hits) == 1
        assert response.facets is not None


class TestContentModels:
    """Test Content-related models"""
    
    def test_content_hit_valid(self):
        """Test ContentHit with valid data"""
        content = ContentHit(
            score=0.923,
            content_id="video123",
            title="Test Video",
            description="Test description",
            video_summary="Test summary",
            tags=["test", "video"],
            duration_sec=3600.0,
            created_at="2026-01-15T10:30:00",
            category="business",
            author="Test Author",
            video_name="test.mp4",
            resolution="1920x1080",
            fps=30.0,
            program_id="prog_001",
            broadcast_date="2026-01-20",
            content_type_id="test_type"
        )
        
        assert content.score == 0.923
        assert content.content_id == "video123"
        assert len(content.tags) == 2
    
    def test_content_hit_optional_fields(self):
        """Test ContentHit with minimal fields"""
        content = ContentHit(
            score=1.0,
            content_id="test",
            title="Test"
        )
        
        assert content.description == ""
        assert content.tags == []
        assert content.duration_sec == 0.0
    
    def test_content_facet_item_valid(self):
        """Test ContentFacetItem with valid data"""
        facet = ContentFacetItem(
            value="business",
            count=8,
            content_ids=["video123", "video124"]
        )
        
        assert facet.value == "business"
        assert facet.count == 8
        assert len(facet.content_ids) == 2
    
    def test_content_search_response_valid(self):
        """Test ContentSearchResponse with valid data"""
        response = ContentSearchResponse(
            total=15,
            hits=[
                ContentHit(
                    score=0.9,
                    content_id="c1",
                    title="Test"
                )
            ],
            facets=ContentFacets(
                category=[], author=[], broadcast_date=[],
                program_id=[], content_type_id=[]
            )
        )
        
        assert response.total == 15
        assert len(response.hits) == 1


class TestIngestModels:
    """Test Ingest-related models"""
    
    def test_face_info_valid(self):
        """Test FaceInfo model"""
        face = FaceInfo(face_id="f001", name="Test Person")
        assert face.face_id == "f001"
        assert face.name == "Test Person"
    
    def test_video_info_valid(self):
        """Test VideoInfo with valid data"""
        video = VideoInfo(
            video_id="video123",
            video_title="Test Video",
            video_name="test.mp4",
            video_summary="Test summary",
            video_tags=["test"],
            video_duration_sec=300.0,
            video_created_at="2026-01-15T10:30:00",
            resolution="1920x1080",
            fps=30.0,
            program_id="prog_001",
            broadcast_date="2026-01-20",
            content_type_id="test_type"
        )
        
        assert video.video_id == "video123"
        assert video.video_title == "Test Video"
        assert len(video.video_tags) == 1
    
    def test_scene_ingest_item_valid(self):
        """Test SceneIngestItem with valid data"""
        from datetime import datetime
        
        scene = SceneIngestItem(
            scene_id="test_scene_001",
            scene_description="Test scene",
            visual_caption="Test caption",
            audio_summarization="Test summary",
            audio_transcription="Test transcript",
            faces=[FaceInfo(face_id="f001", name="Test")],
            start_time_sec=10.0,
            end_time_sec=20.0,
            video=VideoInfo(
                video_id="video123",
                video_title="Test Video"
            ),
            category="test",
            created_date="2026-01-15",
            author="Test Author"
        )
        
        assert scene.scene_id == "test_scene_001"
        assert len(scene.faces) == 1
        assert scene.video.video_id == "video123"
    
    def test_ingest_request_valid(self):
        """Test IngestRequest with valid data"""
        request = IngestRequest(
            scenes=[
                SceneIngestItem(
                    scene_id="s1",
                    scene_description="Test",
                    start_time_sec=0.0,
                    end_time_sec=10.0,
                    video=VideoInfo(
                        video_id="v1",
                        video_title="Test"
                    )
                )
            ]
        )
        
        assert len(request.scenes) == 1
        assert request.scenes[0].scene_id == "s1"
    
    def test_ingest_request_empty_scenes_invalid(self):
        """Test IngestRequest with empty scenes fails"""
        with pytest.raises(ValidationError):
            IngestRequest(scenes=[])
    
    def test_content_ingest_item_valid(self):
        """Test ContentIngestItem with valid data"""
        content = ContentIngestItem(
            content_id="content123",
            title="Test Content",
            description="Test description",
            video_summary="Test summary",
            tags=["test"],
            duration_sec=600.0,
            created_at="2026-01-15T10:30:00",
            category="test",
            author="Test Author",
            video_name="test.mp4",
            resolution="1920x1080",
            fps=30.0,
            program_id="prog_001",
            broadcast_date="2026-01-20",
            content_type_id="test_type"
        )
        
        assert content.content_id == "content123"
        assert content.title == "Test Content"
        assert len(content.tags) == 1
    
    def test_content_ingest_request_valid(self):
        """Test ContentIngestRequest with valid data"""
        request = ContentIngestRequest(
            contents=[
                ContentIngestItem(
                    content_id="c1",
                    title="Test"
                )
            ]
        )
        
        assert len(request.contents) == 1
    
    def test_ingest_response_valid(self):
        """Test IngestResponse with valid data"""
        response = IngestResponse(indexed=5, errors=[])
        assert response.indexed == 5
        assert response.errors == []
        
        response_with_errors = IngestResponse(
            indexed=3,
            errors=["Error 1", "Error 2"]
        )
        assert response_with_errors.indexed == 3
        assert len(response_with_errors.errors) == 2
