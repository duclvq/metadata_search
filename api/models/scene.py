from datetime import datetime

from pydantic import BaseModel, Field


class FaceInfo(BaseModel):
    face_id: str
    name: str


class VideoInfo(BaseModel):
    video_id: str
    video_title: str
    video_name: str = ""
    video_summary: str = ""
    video_tags: list[str] = []
    video_duration_sec: float | None = None
    video_created_at: datetime | None = None
    resolution: str = ""
    fps: float | None = None
    program_id: str = ""
    broadcast_date: str = ""
    content_type_id: str = ""


class SceneIngestItem(BaseModel):
    scene_id: str
    scene_description: str
    visual_caption: str = ""
    audio_summarization: str = ""
    audio_transcription: str = ""
    faces: list[FaceInfo] = []
    start_time_sec: float
    end_time_sec: float
    video: VideoInfo
    category: str = ""
    created_date: str = ""
    author: str = ""


class IngestRequest(BaseModel):
    scenes: list[SceneIngestItem] = Field(..., min_length=1)


class ContentIngestItem(BaseModel):
    content_id: str
    title: str
    description: str = ""
    video_summary: str = ""
    tags: list[str] = []
    duration_sec: float = 0.0
    created_at: str = ""
    category: str = ""
    author: str = ""
    video_name: str = ""
    resolution: str = ""
    fps: float = 0.0
    program_id: str = ""
    broadcast_date: str = ""
    content_type_id: str = ""


class ContentIngestRequest(BaseModel):
    contents: list[ContentIngestItem] = Field(..., min_length=1)


class IngestResponse(BaseModel):
    indexed: int
    errors: list[str] = []
