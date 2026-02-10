from datetime import datetime

from pydantic import BaseModel, Field


class VideoInfo(BaseModel):
    video_id: str
    video_title: str
    video_description: str | None = None
    video_tags: list[str] = []
    video_duration_sec: float | None = None
    video_created_at: datetime | None = None


class SceneIngestItem(BaseModel):
    scene_id: str
    scene_description: str
    start_time_sec: float
    end_time_sec: float
    video: VideoInfo
    category: str = ""
    created_date: str = ""
    author: str = ""


class IngestRequest(BaseModel):
    scenes: list[SceneIngestItem] = Field(..., min_length=1)


class IngestResponse(BaseModel):
    indexed: int
    errors: list[str] = []
