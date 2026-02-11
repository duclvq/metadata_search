from pydantic import BaseModel


class SceneHit(BaseModel):
    score: float
    scene_id: str
    scene_description: str
    start_time_sec: float
    end_time_sec: float
    video_id: str
    video_title: str
    video_description: str | None = None
    video_tags: list[str] = []
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
    tags: list[str] = []
    duration_sec: float = 0.0
    created_at: str = ""
    category: str = ""
    author: str = ""


class ContentFacetItem(BaseModel):
    value: str
    count: int
    content_ids: list[str]


class ContentFacets(BaseModel):
    category: list[ContentFacetItem] = []
    author: list[ContentFacetItem] = []


class ContentSearchResponse(BaseModel):
    total: int
    hits: list[ContentHit]
    facets: ContentFacets | None = None
