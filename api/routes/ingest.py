import json

from fastapi import APIRouter, HTTPException

from api.models.scene import IngestRequest, IngestResponse
from src.config import settings

router = APIRouter(prefix="/v1/scenes", tags=["ingest"])


def _ingest_opensearch(req: IngestRequest) -> IngestResponse:
    from opensearchpy.helpers import bulk

    from src.opensearch_client import get_client

    client = get_client()

    actions = []
    for scene in req.scenes:
        doc = {
            "_index": settings.index_name,
            "_id": scene.scene_id,
            "video_id": scene.video.video_id,
            "video_title": scene.video.video_title,
            "video_description": scene.video.video_description,
            "video_tags": scene.video.video_tags,
            "video_duration_sec": scene.video.video_duration_sec,
            "video_created_at": (
                scene.video.video_created_at.isoformat()
                if scene.video.video_created_at
                else None
            ),
            "scene_id": scene.scene_id,
            "scene_description": scene.scene_description,
            "start_time_sec": scene.start_time_sec,
            "end_time_sec": scene.end_time_sec,
        }
        actions.append(doc)

    try:
        success_count, errors = bulk(client, actions, raise_on_error=False)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenSearch bulk error: {e}")

    error_messages = [str(err) for err in errors] if errors else []
    return IngestResponse(indexed=success_count, errors=error_messages)


def _ingest_milvus(req: IngestRequest) -> IngestResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()

    # Build combined texts for embedding (same logic as OpenSearch ingest pipeline)
    combined_texts = []
    docs = []
    for scene in req.scenes:
        combined_text = f"{scene.scene_description} {scene.video.video_title}".strip()
        combined_texts.append(combined_text)

        docs.append({
            "scene_id": scene.scene_id,
            "scene_description": scene.scene_description,
            "start_time_sec": scene.start_time_sec,
            "end_time_sec": scene.end_time_sec,
            "video_id": scene.video.video_id,
            "video_title": scene.video.video_title,
            "video_description": scene.video.video_description or "",
            "video_tags": json.dumps(scene.video.video_tags),
            "video_duration_sec": scene.video.video_duration_sec or 0.0,
            "video_created_at": (
                scene.video.video_created_at.isoformat()
                if scene.video.video_created_at
                else ""
            ),
            "category": scene.category,
            "created_date": scene.created_date,
            "author": scene.author,
        })

    try:
        vectors = embedding_fn.encode_documents(combined_texts)
        for i, doc in enumerate(docs):
            doc["embedding"] = vectors[i]

        res = client.upsert(
            collection_name=settings.milvus_collection_name,
            data=docs,
        )
        client.flush(collection_name=settings.milvus_collection_name)
        return IngestResponse(indexed=res["upsert_count"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus ingest error: {e}")


@router.post("/ingest", response_model=IngestResponse)
def ingest_scenes(req: IngestRequest):
    if settings.backend == "milvus":
        return _ingest_milvus(req)
    return _ingest_opensearch(req)
