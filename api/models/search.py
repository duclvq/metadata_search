from pydantic import BaseModel


class FaceItem(BaseModel):
    face_id: str
    name: str


class SceneHit(BaseModel):
    score: float
    scene_id: str
    scene_description: str
    visual_caption: str = ""
    audio_summarization: str = ""
    audio_transcription: str = ""
    faces: list[FaceItem] = []
    start_time_sec: float
    end_time_sec: float
    content_id: str
    video_title: str
    video_name: str = ""
    video_summary: str = ""
    video_tags: list[str] = []
    video_duration_sec: float = 0.0
    video_created_at: str = ""
    resolution: str = ""
    fps: float = 0.0
    program_id: str = ""
    broadcast_date: str = ""
    content_type_id: str = ""
    category: str = ""
    created_date: str = ""
    author: str = ""


class FacetItem(BaseModel):
    value: str
    count: int
    scene_ids: list[str]


class Facets(BaseModel):
    category: list[FacetItem] = []
    created_date: list[FacetItem] = []
    author: list[FacetItem] = []
    broadcast_date: list[FacetItem] = []
    program_id: list[FacetItem] = []
    content_type_id: list[FacetItem] = []


class SearchResponse(BaseModel):
    total: int
    hits: list[SceneHit]
    facets: Facets | None = None


# ---------------------------------------------------------------------------
# Content-level models
# ---------------------------------------------------------------------------

class ContentHit(BaseModel):
    score: float
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


class ContentFacetItem(BaseModel):
    value: str
    count: int
    content_ids: list[str]


class ContentFacets(BaseModel):
    category: list[ContentFacetItem] = []
    author: list[ContentFacetItem] = []
    broadcast_date: list[ContentFacetItem] = []
    program_id: list[ContentFacetItem] = []
    content_type_id: list[ContentFacetItem] = []


class ContentSearchResponse(BaseModel):
    total: int
    hits: list[ContentHit]
    facets: ContentFacets | None = None
