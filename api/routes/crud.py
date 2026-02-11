"""
CRUD API for MongoDB video_queue collection.
Every write operation automatically syncs changes to the vector DB.
"""

import logging
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.mongo_client import get_collection
from src.sync_utils import (
    get_scene_ids_from_doc,
    sync_delete_content,
    sync_delete_scenes,
    sync_upsert_content,
    sync_upsert_scenes,
    transform_mongo_doc,
    transform_mongo_doc_to_content,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/videos", tags=["crud"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(doc: dict) -> dict:
    """Convert ObjectId to string for JSON serialization."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class VideoResponse(BaseModel):
    id: str = Field(..., alias="_id")
    unique_id: str = ""
    status: str = ""
    video_path: str = ""
    enriched_data: dict = {}

    model_config = {"populate_by_name": True}


class VideoListResponse(BaseModel):
    total: int
    items: list[dict]


class SyncResult(BaseModel):
    mongo_id: str
    scenes_synced: int


class DeleteResult(BaseModel):
    deleted: bool
    scenes_removed: int


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("", response_model=SyncResult)
def create_video(body: dict[str, Any]):
    """
    Insert a new video document into MongoDB.
    If status is 'completed' and has scenes, auto-syncs to vector DB.
    """
    col = get_collection()
    result = col.insert_one(body)
    mongo_id = str(result.inserted_id)

    # Sync to vector DB
    doc = col.find_one({"_id": result.inserted_id})
    scenes = transform_mongo_doc(doc)
    count = sync_upsert_scenes(scenes)

    content = transform_mongo_doc_to_content(doc)
    if content:
        sync_upsert_content(content)

    return SyncResult(mongo_id=mongo_id, scenes_synced=count)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

@router.get("", response_model=VideoListResponse)
def list_videos(
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List video documents with optional status filter."""
    col = get_collection()
    query = {}
    if status:
        query["status"] = status

    total = col.count_documents(query)
    cursor = col.find(query).skip(skip).limit(limit)
    items = [_serialize(doc) for doc in cursor]

    return VideoListResponse(total=total, items=items)


@router.get("/{unique_id}")
def get_video(unique_id: str):
    """Get a single video document by unique_id."""
    col = get_collection()
    doc = col.find_one({"unique_id": unique_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")
    return _serialize(doc)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{unique_id}", response_model=SyncResult)
def update_video(unique_id: str, body: dict[str, Any]):
    """
    Update a video document by unique_id (partial update via $set).
    Re-syncs scenes to vector DB after update.
    """
    col = get_collection()
    existing = col.find_one({"unique_id": unique_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Video not found")

    # Remove _id from body if present (cannot update _id)
    body.pop("_id", None)
    body.pop("unique_id", None)

    col.update_one({"unique_id": unique_id}, {"$set": body})

    # Re-sync: delete old scenes then upsert new ones
    old_scene_ids = get_scene_ids_from_doc(existing)
    sync_delete_scenes(old_scene_ids)

    updated = col.find_one({"unique_id": unique_id})
    scenes = transform_mongo_doc(updated)
    count = sync_upsert_scenes(scenes)

    content = transform_mongo_doc_to_content(updated)
    if content:
        sync_upsert_content(content)

    return SyncResult(mongo_id=str(existing["_id"]), scenes_synced=count)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{unique_id}", response_model=DeleteResult)
def delete_video(unique_id: str):
    """
    Delete a video document by unique_id.
    Also removes all associated scenes from vector DB.
    """
    col = get_collection()
    doc = col.find_one({"unique_id": unique_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete from vector DB first
    scene_ids = get_scene_ids_from_doc(doc)
    removed = sync_delete_scenes(scene_ids)
    sync_delete_content(unique_id)

    # Delete from MongoDB
    col.delete_one({"_id": doc["_id"]})

    return DeleteResult(deleted=True, scenes_removed=removed)


# ---------------------------------------------------------------------------
# MANUAL SYNC
# ---------------------------------------------------------------------------

@router.post("/{unique_id}/sync", response_model=SyncResult)
def sync_video(unique_id: str):
    """
    Manually trigger sync of a video's scenes to the vector DB.
    Useful for re-indexing after external MongoDB changes.
    """
    col = get_collection()
    doc = col.find_one({"unique_id": unique_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete old then re-ingest
    scene_ids = get_scene_ids_from_doc(doc)
    sync_delete_scenes(scene_ids)

    scenes = transform_mongo_doc(doc)
    count = sync_upsert_scenes(scenes)

    content = transform_mongo_doc_to_content(doc)
    if content:
        sync_upsert_content(content)

    return SyncResult(mongo_id=str(doc["_id"]), scenes_synced=count)


@router.post("/sync-all", response_model=dict)
def sync_all_videos():
    """
    Full re-sync: transform all completed videos and upsert to vector DB.
    """
    col = get_collection()
    docs = col.find({"status": "completed"})

    total_scenes = 0
    total_videos = 0
    total_contents = 0
    for doc in docs:
        scenes = transform_mongo_doc(doc)
        if scenes:
            sync_upsert_scenes(scenes)
            total_scenes += len(scenes)
            total_videos += 1

        content = transform_mongo_doc_to_content(doc)
        if content:
            sync_upsert_content(content)
            total_contents += 1

    return {"videos_synced": total_videos, "scenes_synced": total_scenes, "contents_synced": total_contents}
