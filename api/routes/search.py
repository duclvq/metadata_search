from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.models.search import (
    ContentFacets,
    ContentHit,
    ContentSearchResponse,
    Facets,
    SceneHit,
    SearchResponse,
)
from src.config import settings

router = APIRouter(prefix="/v1/search", tags=["search"])


# ---- OpenSearch helpers (scene only) ----

def _parse_opensearch_hits(raw_hits: list[dict]) -> list[SceneHit]:
    results = []
    for hit in raw_hits:
        src = hit["_source"]
        faces = src.get("faces", [])
        if isinstance(faces, str):
            import json as _json
            try:
                faces = _json.loads(faces)
            except Exception:
                faces = []
        results.append(
            SceneHit(
                score=hit.get("_score", 0.0),
                scene_id=src["scene_id"],
                scene_description=src["scene_description"],
                visual_caption=src.get("visual_caption", ""),
                audio_summarization=src.get("audio_summarization", ""),
                audio_transcription=src.get("audio_transcription", ""),
                faces=faces,
                start_time_sec=src["start_time_sec"],
                end_time_sec=src["end_time_sec"],
                video_id=src["video_id"],
                video_title=src["video_title"],
                video_name=src.get("video_name", ""),
                video_summary=src.get("video_summary", ""),
                video_tags=src.get("video_tags", []),
                video_duration_sec=src.get("video_duration_sec", 0.0),
                video_created_at=src.get("video_created_at", ""),
                resolution=src.get("resolution", ""),
                fps=src.get("fps", 0.0),
                program_id=src.get("program_id", ""),
                broadcast_date=src.get("broadcast_date", ""),
                content_type_id=src.get("content_type_id", ""),
                category=src.get("category", ""),
                created_date=src.get("created_date", ""),
                author=src.get("author", ""),
            )
        )
    return results


def _opensearch_semantic(query_text: str, k: int) -> SearchResponse:
    from src.opensearch_client import get_client
    from src.queries import build_semantic_query

    client = get_client()
    query = build_semantic_query(query_text, k)

    try:
        response = client.search(index=settings.index_name, body=query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenSearch error: {e}")

    hits = _parse_opensearch_hits(response["hits"]["hits"])
    total = response["hits"]["total"]["value"]
    return SearchResponse(total=total, hits=hits)


def _opensearch_hybrid(query_text: str, k: int) -> SearchResponse:
    from src.opensearch_client import get_client
    from src.queries import build_hybrid_query

    client = get_client()
    query = build_hybrid_query(query_text, k)

    try:
        response = client.search(
            index=settings.index_name,
            body=query,
            params={"search_pipeline": settings.search_pipeline_name},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenSearch error: {e}")

    hits = _parse_opensearch_hits(response["hits"]["hits"])
    total = response["hits"]["total"]["value"]
    return SearchResponse(total=total, hits=hits)


# ---- Milvus scene helpers ----

def _milvus_scene_semantic(query_text: str, k: int, filter_expr: str | None = None) -> SearchResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_queries import search_scene_semantic

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()
    try:
        result = search_scene_semantic(client, embedding_fn, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [SceneHit(**h) for h in result["hits"]]
    facets = Facets(**result["facets"])
    return SearchResponse(total=result["total"], hits=hits, facets=facets)


def _milvus_scene_fulltext(query_text: str, k: int, filter_expr: str | None = None) -> SearchResponse:
    from src.milvus_client import get_milvus_client
    from src.milvus_queries import search_scene_fulltext

    client = get_milvus_client()
    try:
        result = search_scene_fulltext(client, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [SceneHit(**h) for h in result["hits"]]
    facets = Facets(**result["facets"])
    return SearchResponse(total=result["total"], hits=hits, facets=facets)


def _milvus_scene_hybrid(query_text: str, k: int, filter_expr: str | None = None) -> SearchResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_queries import search_scene_hybrid

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()
    try:
        result = search_scene_hybrid(client, embedding_fn, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [SceneHit(**h) for h in result["hits"]]
    facets = Facets(**result["facets"])
    return SearchResponse(total=result["total"], hits=hits, facets=facets)


# ---- Milvus content helpers ----

def _milvus_content_semantic(query_text: str, k: int, filter_expr: str | None = None) -> ContentSearchResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_queries import search_content_semantic

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()
    try:
        result = search_content_semantic(client, embedding_fn, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [ContentHit(**h) for h in result["hits"]]
    facets = ContentFacets(**result["facets"])
    return ContentSearchResponse(total=result["total"], hits=hits, facets=facets)


def _milvus_content_fulltext(query_text: str, k: int, filter_expr: str | None = None) -> ContentSearchResponse:
    from src.milvus_client import get_milvus_client
    from src.milvus_queries import search_content_fulltext

    client = get_milvus_client()
    try:
        result = search_content_fulltext(client, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [ContentHit(**h) for h in result["hits"]]
    facets = ContentFacets(**result["facets"])
    return ContentSearchResponse(total=result["total"], hits=hits, facets=facets)


def _milvus_content_hybrid(query_text: str, k: int, filter_expr: str | None = None) -> ContentSearchResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_queries import search_content_hybrid

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()
    try:
        result = search_content_hybrid(client, embedding_fn, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")
    hits = [ContentHit(**h) for h in result["hits"]]
    facets = ContentFacets(**result["facets"])
    return ContentSearchResponse(total=result["total"], hits=hits, facets=facets)


# ---- Scene search (unified) ----

@router.get("/scene", response_model=SearchResponse)
def scene_search(
    query_text: str = Query(..., min_length=1),
    k: int = Query(default=10, ge=1, le=100),
    search_type: str = Query(default="hybrid", pattern="^(semantic|fulltext|hybrid)$"),
):
    if search_type == "fulltext":
        if settings.backend != "milvus":
            raise HTTPException(status_code=501, detail="Full-text search only supports Milvus backend")
        return _milvus_scene_fulltext(query_text, k)

    if search_type == "semantic":
        if settings.backend == "milvus":
            return _milvus_scene_semantic(query_text, k)
        return _opensearch_semantic(query_text, k)

    # hybrid (default)
    if settings.backend == "milvus":
        return _milvus_scene_hybrid(query_text, k)
    return _opensearch_hybrid(query_text, k)


# ---- Content search (unified) ----

@router.get("/content", response_model=ContentSearchResponse)
def content_search(
    query_text: str = Query(..., min_length=1),
    k: int = Query(default=10, ge=1, le=100),
    search_type: str = Query(default="hybrid", pattern="^(semantic|fulltext|hybrid)$"),
):
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Content search only supports Milvus backend")

    if search_type == "fulltext":
        return _milvus_content_fulltext(query_text, k)
    if search_type == "semantic":
        return _milvus_content_semantic(query_text, k)
    return _milvus_content_hybrid(query_text, k)


# ---- Scene filter ----

class SceneFilterRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    scene_ids: list[str] = Field(..., min_length=1)
    k: int = Field(default=10, ge=1, le=100)
    search_type: str = Field(default="semantic", pattern="^(semantic|fulltext|hybrid)$")


@router.post("/scene/filter", response_model=SearchResponse)
def scene_filter_search(req: SceneFilterRequest):
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Filter API only supports Milvus backend")
    ids_str = ", ".join(f'"{sid}"' for sid in req.scene_ids)
    filter_expr = f"scene_id in [{ids_str}]"

    if req.search_type == "hybrid":
        return _milvus_scene_hybrid(req.query_text, req.k, filter_expr)
    if req.search_type == "fulltext":
        return _milvus_scene_fulltext(req.query_text, req.k, filter_expr)
    return _milvus_scene_semantic(req.query_text, req.k, filter_expr)


# ---- Content filter ----

class ContentFilterRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    content_ids: list[str] = Field(..., min_length=1)
    k: int = Field(default=10, ge=1, le=100)
    search_type: str = Field(default="semantic", pattern="^(semantic|fulltext|hybrid)$")


@router.post("/content/filter", response_model=ContentSearchResponse)
def content_filter_search(req: ContentFilterRequest):
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Filter API only supports Milvus backend")
    ids_str = ", ".join(f'"{cid}"' for cid in req.content_ids)
    filter_expr = f"content_id in [{ids_str}]"

    if req.search_type == "hybrid":
        return _milvus_content_hybrid(req.query_text, req.k, filter_expr)
    if req.search_type == "fulltext":
        return _milvus_content_fulltext(req.query_text, req.k, filter_expr)
    return _milvus_content_semantic(req.query_text, req.k, filter_expr)


# ---- List endpoints (unchanged) ----

@router.get("/scene/list")
def list_scenes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=1000),
):
    """List scenes currently indexed in the vector DB."""
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="List API only supports Milvus backend")

    from src.milvus_client import get_milvus_client
    from src.milvus_queries import SCENE_OUTPUT_FIELDS

    client = get_milvus_client()
    results = client.query(
        collection_name=settings.milvus_collection_name,
        filter="",
        output_fields=SCENE_OUTPUT_FIELDS,
        limit=limit,
        offset=skip,
    )

    import json
    items = []
    for r in results:
        tags = r.get("video_tags", "[]")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []
        r["video_tags"] = tags
        faces = r.get("faces", "[]")
        if isinstance(faces, str):
            try:
                faces = json.loads(faces)
            except Exception:
                faces = []
        r["faces"] = faces
        items.append(r)

    return {"total": len(items), "items": items}


@router.get("/content/list")
def list_contents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=1000),
):
    """List contents (videos) currently indexed in the vector DB."""
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="List API only supports Milvus backend")

    from src.milvus_client import get_milvus_client
    from src.milvus_queries import CONTENT_OUTPUT_FIELDS

    client = get_milvus_client()
    results = client.query(
        collection_name=settings.milvus_content_collection_name,
        filter="",
        output_fields=CONTENT_OUTPUT_FIELDS,
        limit=limit,
        offset=skip,
    )

    import json
    items = []
    for r in results:
        tags = r.get("tags", "[]")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []
        r["tags"] = tags
        items.append(r)

    return {"total": len(items), "items": items}
