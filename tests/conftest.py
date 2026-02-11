"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API"""
    from api.main import app
    return TestClient(app)


@pytest.fixture
def sample_scene_data():
    """Sample scene ingest data"""
    return {
        "scenes": [
            {
                "scene_id": "test_video_001_scene_001",
                "scene_description": "Test scene description",
                "visual_caption": "Test visual caption",
                "audio_summarization": "Test audio summary",
                "audio_transcription": "Test audio transcript",
                "faces": [
                    {"face_id": "f001", "name": "Test Person A"}
                ],
                "start_time_sec": 10.5,
                "end_time_sec": 25.3,
                "category": "test_category",
                "created_date": "2026-01-15",
                "author": "Test Author",
                "video": {
                    "video_id": "test_video_001",
                    "video_title": "Test Video Title",
                    "video_name": "test_video.mp4",
                    "video_summary": "Test video summary",
                    "video_tags": ["test", "sample"],
                    "video_duration_sec": 300.0,
                    "video_created_at": "2026-01-15T10:30:00",
                    "resolution": "1920x1080",
                    "fps": 30.0,
                    "program_id": "prog_test",
                    "broadcast_date": "2026-01-20",
                    "content_type_id": "test_type"
                }
            }
        ]
    }


@pytest.fixture
def sample_content_data():
    """Sample content ingest data"""
    return {
        "contents": [
            {
                "content_id": "test_content_001",
                "title": "Test Content Title",
                "description": "Test content description",
                "video_summary": "Test content summary",
                "tags": ["test", "content"],
                "duration_sec": 600.0,
                "created_at": "2026-01-15T10:30:00",
                "category": "test_category",
                "author": "Test Author",
                "video_name": "test_content.mp4",
                "resolution": "1920x1080",
                "fps": 30.0,
                "program_id": "prog_test",
                "broadcast_date": "2026-01-20",
                "content_type_id": "test_type"
            }
        ]
    }
