"""
Shared utilities for transforming MongoDB documents to vector DB format
and syncing (upsert / delete) with the configured vector backend.
"""

import json
import logging

from src.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

def parse_time_to_sec(time_str: str) -> float:
    """Convert 'HH:MM:SS.mmm' to seconds."""
    parts = time_str.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def transform_mongo_doc(doc: dict) -> list[dict]:
    """
    Transform a single MongoDB video_queue document into a list of
    SceneIngestItem-compatible dicts ready for the ingest pipeline.

    Returns an empty list if the document has no scenes or is not completed.
    """
    if doc.get("status") != "completed":
        return []

    enriched = doc.get("enriched_data", {})
    scene_list = enriched.get("scene_list", [])
    if not scene_list:
        return []

    # Audio scene summaries are keyed by cluster index ("0", "1", ...)
    scene_summaries: dict = enriched.get("audio", {}).get("scene_summaries", {})

    video_id = doc.get("unique_id", str(doc.get("_id", "")))
    video_title = doc.get("title", "")
    video_info = enriched.get("video_info", {})

    # Try to parse duration from video_info
    video_duration_sec = doc.get("video_duration_sec")
    if video_duration_sec is None:
        dur_str = video_info.get("duration", "")
        if dur_str and ":" in dur_str:
            try:
                video_duration_sec = parse_time_to_sec(dur_str)
            except Exception:
                video_duration_sec = None

    video_created_at = doc.get("video_created_at")
    video_tags = doc.get("video_tags", [])

    # Audio full transcription as video_description fallback
    video_description = enriched.get("audio", {}).get("metadata", {}).get("transcription", "")
    if not video_description:
        video_description = enriched.get("audio", {}).get("transcription", "")

    scenes = []
    for idx, scene in enumerate(scene_list):
        caption = scene.get("scene_captioning", "")
        # Try to get audio summary for this scene's cluster
        audio_summary = scene_summaries.get(str(idx), "")
        description = f"{caption}\n{audio_summary}".strip() if audio_summary else caption

        # Parse time — handle both "HH:MM:SS.mmm" string and numeric formats
        start_raw = scene.get("start", 0)
        end_raw = scene.get("end", 0)
        if isinstance(start_raw, str):
            start_sec = parse_time_to_sec(start_raw)
        else:
            start_sec = float(start_raw)
        if isinstance(end_raw, str):
            end_sec = parse_time_to_sec(end_raw)
        else:
            end_sec = float(end_raw)

        scenes.append({
            "scene_id": scene["scene_id"],
            "scene_description": description,
            "start_time_sec": start_sec,
            "end_time_sec": end_sec,
            "video": {
                "video_id": video_id,
                "video_title": video_title,
                "video_description": video_description,
                "video_tags": video_tags,
                "video_duration_sec": video_duration_sec,
                "video_created_at": video_created_at,
            },
            "category": scene.get("category", scene.get("video_type", "")),
            "created_date": scene.get("created_date", ""),
            "author": scene.get("author", ""),
        })

    return scenes


def get_scene_ids_from_doc(doc: dict) -> list[str]:
    """Extract all scene_ids from a MongoDB document."""
    enriched = doc.get("enriched_data", {})
    return [s["scene_id"] for s in enriched.get("scene_list", []) if "scene_id" in s]


# ---------------------------------------------------------------------------
# Vector DB sync operations
# ---------------------------------------------------------------------------

def sync_upsert_scenes(scenes: list[dict]) -> int:
    """
    Upsert scenes to the configured vector backend.
    Returns the number of successfully indexed scenes.
    """
    if not scenes:
        return 0

    if settings.backend == "milvus":
        return _upsert_milvus(scenes)
    return _upsert_opensearch(scenes)


def sync_delete_scenes(scene_ids: list[str]) -> int:
    """
    Delete scenes from the configured vector backend by scene_id.
    Returns the number of deleted scenes.
    """
    if not scene_ids:
        return 0

    if settings.backend == "milvus":
        return _delete_milvus(scene_ids)
    return _delete_opensearch(scene_ids)


# ---------------------------------------------------------------------------
# Milvus backend
# ---------------------------------------------------------------------------

def _upsert_milvus(scenes: list[dict]) -> int:
    from src.milvus_client import get_embedding_fn, get_milvus_client

    client = get_milvus_client()
    embedding_fn = get_embedding_fn()

    combined_texts = []
    docs = []
    for scene in scenes:
        video = scene["video"]
        combined_text = f"{scene['scene_description']} {video['video_title']}".strip()
        combined_texts.append(combined_text)

        docs.append({
            "scene_id": scene["scene_id"],
            "scene_description": scene["scene_description"],
            "start_time_sec": scene["start_time_sec"],
            "end_time_sec": scene["end_time_sec"],
            "video_id": video["video_id"],
            "video_title": video["video_title"],
            "video_description": video.get("video_description") or "",
            "video_tags": json.dumps(video.get("video_tags", [])),
            "video_duration_sec": video.get("video_duration_sec") or 0.0,
            "video_created_at": (
                video["video_created_at"].isoformat()
                if hasattr(video.get("video_created_at"), "isoformat")
                else (video.get("video_created_at") or "")
            ),
            "category": scene.get("category", ""),
            "created_date": scene.get("created_date", ""),
            "author": scene.get("author", ""),
        })

    vectors = embedding_fn.encode_documents(combined_texts)
    for i, doc in enumerate(docs):
        doc["embedding"] = vectors[i]

    res = client.upsert(
        collection_name=settings.milvus_collection_name,
        data=docs,
    )
    client.flush(collection_name=settings.milvus_collection_name)
    count = res.get("upsert_count", len(docs))
    logger.info("Milvus upsert: %d scenes", count)
    return count


def _delete_milvus(scene_ids: list[str]) -> int:
    from src.milvus_client import get_milvus_client

    client = get_milvus_client()
    ids_str = ", ".join(f'"{sid}"' for sid in scene_ids)
    filter_expr = f"scene_id in [{ids_str}]"
    client.delete(
        collection_name=settings.milvus_collection_name,
        filter=filter_expr,
    )
    client.flush(collection_name=settings.milvus_collection_name)
    logger.info("Milvus delete: %d scenes", len(scene_ids))
    return len(scene_ids)


# ---------------------------------------------------------------------------
# OpenSearch backend
# ---------------------------------------------------------------------------

def _upsert_opensearch(scenes: list[dict]) -> int:
    from opensearchpy.helpers import bulk
    from src.opensearch_client import get_client

    client = get_client()
    actions = []
    for scene in scenes:
        video = scene["video"]
        doc = {
            "_index": settings.index_name,
            "_id": scene["scene_id"],
            "video_id": video["video_id"],
            "video_title": video["video_title"],
            "video_description": video.get("video_description"),
            "video_tags": video.get("video_tags", []),
            "video_duration_sec": video.get("video_duration_sec"),
            "video_created_at": (
                video["video_created_at"].isoformat()
                if hasattr(video.get("video_created_at"), "isoformat")
                else video.get("video_created_at")
            ),
            "scene_id": scene["scene_id"],
            "scene_description": scene["scene_description"],
            "start_time_sec": scene["start_time_sec"],
            "end_time_sec": scene["end_time_sec"],
        }
        actions.append(doc)

    success_count, errors = bulk(client, actions, raise_on_error=False)
    if errors:
        for err in errors:
            logger.error("OpenSearch bulk error: %s", err)
    logger.info("OpenSearch upsert: %d scenes", success_count)
    return success_count


def _delete_opensearch(scene_ids: list[str]) -> int:
    from src.opensearch_client import get_client

    client = get_client()
    deleted = 0
    for sid in scene_ids:
        try:
            client.delete(index=settings.index_name, id=sid, ignore=[404])
            deleted += 1
        except Exception as e:
            logger.error("OpenSearch delete error for %s: %s", sid, e)
    logger.info("OpenSearch delete: %d scenes", deleted)
    return deleted
