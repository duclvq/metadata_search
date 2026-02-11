"""
Face Search API — search scenes by face images or face names.

Endpoints:
    POST /v1/face_search          — upload face images or provide face names
    POST /v1/face_search/filter   — refine results with facet filters
"""

import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from api.models.search import Facets, SceneHit, SearchResponse
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/face_search", tags=["face_search"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_face_filter(face_names: list[str]) -> str:
    """Build Milvus filter expression to match scenes containing given faces."""
    parts = []
    for name in face_names:
        escaped = name.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'faces like "%{escaped}%"')
    if len(parts) == 1:
        return parts[0]
    return " or ".join(f"({p})" for p in parts)


def _build_facet_filter(field_values: dict[str, list[str] | None]) -> str | None:
    """Build Milvus filter from facet field–value pairs."""
    conditions: list[str] = []
    for field, values in field_values.items():
        if not values:
            continue
        clean = [v for v in values if v]
        if not clean:
            continue
        if len(clean) == 1:
            val = clean[0].replace("\\", "\\\\").replace('"', '\\"')
            conditions.append(f'{field} == "{val}"')
        else:
            quoted = ", ".join(
                f'"{v.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"'
                for v in clean
            )
            conditions.append(f"{field} in [{quoted}]")
    return " and ".join(conditions) if conditions else None


def _combine_filters(*exprs: str | None) -> str | None:
    """Combine multiple filter expressions with AND."""
    parts = [e for e in exprs if e]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return " and ".join(f"({p})" for p in parts)


def _parse_entity(entity: dict) -> dict:
    """Parse a raw Milvus entity into a SceneHit-compatible dict."""
    tags = entity.get("video_tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []

    faces = entity.get("faces", "[]")
    if isinstance(faces, str):
        try:
            faces = json.loads(faces)
        except Exception:
            faces = []

    return {
        "score": 1.0,
        "scene_id": entity.get("scene_id", ""),
        "scene_description": entity.get("scene_description", ""),
        "visual_caption": entity.get("visual_caption", ""),
        "audio_summarization": entity.get("audio_summarization", ""),
        "audio_transcription": entity.get("audio_transcription", ""),
        "faces": faces,
        "start_time_sec": entity.get("start_time_sec", 0.0),
        "end_time_sec": entity.get("end_time_sec", 0.0),
        "content_id": entity.get("video_id", ""),
        "video_title": entity.get("video_title", ""),
        "video_name": entity.get("video_name", ""),
        "video_summary": entity.get("video_summary", ""),
        "video_tags": tags,
        "video_duration_sec": entity.get("video_duration_sec", 0.0),
        "video_created_at": entity.get("video_created_at", ""),
        "resolution": entity.get("resolution", ""),
        "fps": entity.get("fps", 0.0),
        "program_id": entity.get("program_id", ""),
        "broadcast_date": entity.get("broadcast_date", ""),
        "content_type_id": entity.get("content_type_id", ""),
        "category": entity.get("category", ""),
        "created_date": entity.get("created_date", ""),
        "author": entity.get("author", ""),
    }


def _search_scenes_by_face(
    face_names: list[str],
    k: int,
    extra_filter: str | None = None,
) -> SearchResponse:
    """Query Milvus scenes whose *faces* field contains the given names."""
    from src.milvus_client import get_milvus_client
    from src.milvus_queries import SCENE_OUTPUT_FIELDS, build_scene_facets

    client = get_milvus_client()

    face_filter = _build_face_filter(face_names)
    combined = _combine_filters(face_filter, extra_filter)

    try:
        results = client.query(
            collection_name=settings.milvus_collection_name,
            filter=combined,
            output_fields=SCENE_OUTPUT_FIELDS,
            limit=k,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")

    hits = [_parse_entity(r) for r in results]
    scene_hits = [SceneHit(**h) for h in hits]
    facets = Facets(**build_scene_facets(hits))

    return SearchResponse(total=len(scene_hits), hits=scene_hits, facets=facets)


# ---------------------------------------------------------------------------
# Face recognition placeholder
# ---------------------------------------------------------------------------

async def _detect_faces_from_images(images: list[UploadFile]) -> list[str]:
    """
    Detect and identify faces from uploaded images.

    ⚠ Placeholder — replace with a real face-recognition backend
    (insightface, face_recognition, DeepFace, …) for production use.

    Returns a list of recognised face names.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Image-based face recognition is not yet configured. "
            "Provide face_names instead, or integrate a recognition model "
            "(insightface, face_recognition, DeepFace, etc.)."
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=SearchResponse, summary="Search scenes by face")
async def face_search(
    images: list[UploadFile] = File(default=[], description="Face images to search for"),
    face_names: list[str] = Form(default=[], description="Face names to search for"),
    k: int = Form(default=10, ge=1, le=100, description="Max results"),
):
    """
    Search scenes that contain specific faces.

    Provide **images** (face recognition) and/or **face_names** (direct match).
    At least one must be given.
    """
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Face search only supports Milvus backend")

    names: list[str] = []

    # Image-based detection
    real_images = [img for img in images if img.filename]
    if real_images:
        detected = await _detect_faces_from_images(real_images)
        names.extend(detected)

    # Direct name input
    if face_names:
        names.extend(face_names)

    if not names:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one face image or face_names.",
        )

    return _search_scenes_by_face(names, k)


# ---- Filter (post-search refinement) ----

class FaceFilterRequest(BaseModel):
    face_names: list[str] = Field(..., min_length=1)
    category: list[str] | None = None
    author: list[str] | None = None
    created_date: list[str] | None = None
    broadcast_date: list[str] | None = None
    program_id: list[str] | None = None
    content_type_id: list[str] | None = None
    k: int = Field(default=10, ge=1, le=100)


@router.post("/filter", response_model=SearchResponse, summary="Filter face search results")
def face_filter_search(req: FaceFilterRequest):
    """
    Refine face-search results with additional facet filters
    (category, author, broadcast_date, program_id, content_type_id).
    """
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Face search only supports Milvus backend")

    extra_filter = _build_facet_filter(
        {
            "category": req.category,
            "author": req.author,
            "created_date": req.created_date,
            "broadcast_date": req.broadcast_date,
            "program_id": req.program_id,
            "content_type_id": req.content_type_id,
        }
    )

    return _search_scenes_by_face(req.face_names, req.k, extra_filter)
