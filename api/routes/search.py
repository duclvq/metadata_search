from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.models.search import Facets, SceneHit, SearchResponse
from src.config import settings

router = APIRouter(prefix="/v1/search", tags=["search"])


# ---- OpenSearch helpers ----

def _parse_opensearch_hits(raw_hits: list[dict]) -> list[SceneHit]:
    results = []
    for hit in raw_hits:
        src = hit["_source"]
        results.append(
            SceneHit(
                score=hit.get("_score", 0.0),
                scene_id=src["scene_id"],
                scene_description=src["scene_description"],
                start_time_sec=src["start_time_sec"],
                end_time_sec=src["end_time_sec"],
                video_id=src["video_id"],
                video_title=src["video_title"],
                video_description=src.get("video_description"),
                video_tags=src.get("video_tags", []),
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


# ---- Milvus helpers ----

def _milvus_search(query_text: str, k: int, filter_expr: str | None = None) -> SearchResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_queries import search_semantic

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()

    try:
        result = search_semantic(client, embedding_fn, query_text, k, filter_expr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus error: {e}")

    hits = [SceneHit(**h) for h in result["hits"]]
    facets = Facets(**result["facets"])
    return SearchResponse(total=result["total"], hits=hits, facets=facets)


# ---- Endpoints ----

@router.get("/semantic", response_model=SearchResponse)
def semantic_search(
    query_text: str = Query(..., min_length=1),
    k: int = Query(default=10, ge=1, le=100),
):
    if settings.backend == "milvus":
        return _milvus_search(query_text, k)
    return _opensearch_semantic(query_text, k)


@router.get("/hybrid", response_model=SearchResponse)
def hybrid_search(
    query_text: str = Query(..., min_length=1),
    k: int = Query(default=10, ge=1, le=100),
):
    if settings.backend == "milvus":
        return _milvus_search(query_text, k)
    return _opensearch_hybrid(query_text, k)


# ---- Filter API ----

class FilterRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    scene_ids: list[str] = Field(..., min_length=1)
    k: int = Field(default=10, ge=1, le=100)


@router.post("/filter", response_model=SearchResponse)
def filter_search(req: FilterRequest):
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Filter API only supports Milvus backend")

    # Build Milvus filter expression: scene_id in ["id1", "id2", ...]
    ids_str = ", ".join(f'"{sid}"' for sid in req.scene_ids)
    filter_expr = f"scene_id in [{ids_str}]"

    return _milvus_search(req.query_text, req.k, filter_expr)
