import json

from fastapi import APIRouter, HTTPException

from api.models.scene import ContentIngestRequest, IngestRequest, IngestResponse
from src.config import settings

router = APIRouter(prefix="/v1", tags=["ingest"])


def _ingest_opensearch(req: IngestRequest) -> IngestResponse:
    from opensearchpy.helpers import bulk

    from src.opensearch_client import get_client

    client = get_client()

    actions = []
    for scene in req.scenes:
        faces_data = [{"face_id": f.face_id, "name": f.name} for f in scene.faces]
        doc = {
            "_index": settings.index_name,
            "_id": scene.scene_id,
            "video_id": scene.video.video_id,
            "video_title": scene.video.video_title,
            "video_name": scene.video.video_name,
            "video_summary": scene.video.video_summary,
            "video_tags": scene.video.video_tags,
            "video_duration_sec": scene.video.video_duration_sec,
            "video_created_at": (
                scene.video.video_created_at.isoformat()
                if scene.video.video_created_at
                else None
            ),
            "resolution": scene.video.resolution,
            "fps": scene.video.fps or 0.0,
            "program_id": scene.video.program_id,
            "broadcast_date": scene.video.broadcast_date,
            "content_type_id": scene.video.content_type_id,
            "scene_id": scene.scene_id,
            "scene_description": scene.scene_description,
            "visual_caption": scene.visual_caption,
            "audio_summarization": scene.audio_summarization,
            "audio_transcription": scene.audio_transcription,
            "faces": json.dumps(faces_data, ensure_ascii=False),
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

        faces_data = [{"face_id": f.face_id, "name": f.name} for f in scene.faces]

        docs.append({
            "scene_id": scene.scene_id,
            "scene_description": scene.scene_description,
            "visual_caption": scene.visual_caption,
            "audio_summarization": scene.audio_summarization,
            "audio_transcription": scene.audio_transcription,
            "faces": json.dumps(faces_data, ensure_ascii=False),
            "start_time_sec": scene.start_time_sec,
            "end_time_sec": scene.end_time_sec,
            "video_id": scene.video.video_id,
            "video_title": scene.video.video_title,
            "video_name": scene.video.video_name,
            "video_summary": scene.video.video_summary,
            "video_tags": json.dumps(scene.video.video_tags),
            "video_duration_sec": scene.video.video_duration_sec or 0.0,
            "video_created_at": (
                scene.video.video_created_at.isoformat()
                if scene.video.video_created_at
                else ""
            ),
            "resolution": scene.video.resolution,
            "fps": scene.video.fps or 0.0,
            "program_id": scene.video.program_id,
            "broadcast_date": scene.video.broadcast_date,
            "content_type_id": scene.video.content_type_id,
            "category": scene.category,
            "created_date": scene.created_date,
            "author": scene.author,
            "bm25_text": combined_text,
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


@router.post("/scenes/ingest", response_model=IngestResponse)
def ingest_scenes(req: IngestRequest):
    if settings.backend == "milvus":
        return _ingest_milvus(req)
    return _ingest_opensearch(req)


def _ingest_milvus_content(req: ContentIngestRequest) -> IngestResponse:
    from src.milvus_client import get_embedding_fn, get_milvus_client

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()

    combined_texts = []
    docs = []
    for item in req.contents:
        tags_text = " ".join(item.tags)
        combined_text = f"{item.title} {item.description} {tags_text}".strip()
        combined_texts.append(combined_text)

        docs.append({
            "content_id": item.content_id,
            "title": item.title,
            "description": item.description,
            "video_summary": item.video_summary,
            "tags": json.dumps(item.tags),
            "duration_sec": item.duration_sec,
            "created_at": item.created_at,
            "category": item.category,
            "author": item.author,
            "video_name": item.video_name,
            "resolution": item.resolution,
            "fps": item.fps,
            "program_id": item.program_id,
            "broadcast_date": item.broadcast_date,
            "content_type_id": item.content_type_id,
            "bm25_text": combined_text,
        })

    try:
        vectors = embedding_fn.encode_documents(combined_texts)
        for i, doc in enumerate(docs):
            doc["embedding"] = vectors[i]

        res = client.upsert(
            collection_name=settings.milvus_content_collection_name,
            data=docs,
        )
        client.flush(collection_name=settings.milvus_content_collection_name)
        return IngestResponse(indexed=res["upsert_count"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Milvus content ingest error: {e}")


@router.post("/contents/ingest", response_model=IngestResponse)
def ingest_contents(req: ContentIngestRequest):
    if settings.backend != "milvus":
        raise HTTPException(status_code=501, detail="Content ingest only supports Milvus backend")
    return _ingest_milvus_content(req)
