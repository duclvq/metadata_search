"""
MongoDB Change Stream Watcher — bridges MongoDB ↔ Vector DB.

Watches the `video_queue` collection for insert / update / delete events.
When a video document changes and its status is "completed", the watcher
transforms the scenes and upserts them into the configured vector backend
(Milvus or OpenSearch).  Deleted documents trigger scene removal.

Reliability features:
  - Resume token persisted to disk → survives restarts without missing events
  - Exponential backoff on connection errors → auto-reconnects
  - Graceful shutdown on SIGINT / SIGTERM
  - Structured logging

Usage:
    python -m scripts.mongo_watcher                  # foreground
    python -m scripts.mongo_watcher --full-sync      # one-time full re-sync then watch
    python -m scripts.mongo_watcher --reset-token     # discard saved position

Can be installed as a Windows service via nssm:
    nssm install MongoWatcher "C:\\path\\python.exe" "-m scripts.mongo_watcher"
    nssm set MongoWatcher AppDirectory "D:\\py_source\\metadata_search"
"""

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path when running directly
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from pymongo.errors import PyMongoError

from src.config import settings
from src.mongo_client import get_collection, get_mongo_client
from src.sync_utils import (
    get_scene_ids_from_doc,
    sync_delete_content,
    sync_delete_scenes,
    sync_upsert_content,
    sync_upsert_scenes,
    transform_mongo_doc,
    transform_mongo_doc_to_content,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("mongo_watcher")

# ---------------------------------------------------------------------------
# Resume token persistence
# ---------------------------------------------------------------------------

_token_path = Path(settings.mongo_resume_token_path)


def _save_token(token: dict) -> None:
    _token_path.write_text(json.dumps(token), encoding="utf-8")


def _load_token() -> dict | None:
    if _token_path.exists():
        try:
            return json.loads(_token_path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Corrupt resume token file — starting from latest.")
    return None


def _clear_token() -> None:
    if _token_path.exists():
        _token_path.unlink()
        logger.info("Resume token cleared.")


# ---------------------------------------------------------------------------
# Vector backend setup
# ---------------------------------------------------------------------------

def _ensure_backend() -> None:
    """Initialise the vector backend (index / collection) once."""
    if settings.backend == "milvus":
        from src.milvus_client import get_embedding_fn, get_milvus_client
        from src.milvus_manager import ensure_collection

        client = get_milvus_client()
        ensure_collection(client)
        get_embedding_fn()  # pre-load model
        logger.info("Milvus backend ready.")
    else:
        from src.index_manager import ensure_index, ensure_ingest_pipeline, ensure_search_pipeline
        from src.opensearch_client import get_client

        client = get_client()
        ensure_ingest_pipeline(client)
        ensure_index(client)
        ensure_search_pipeline(client)
        logger.info("OpenSearch backend ready.")


# ---------------------------------------------------------------------------
# Full sync (cold start or --full-sync)
# ---------------------------------------------------------------------------

def full_sync() -> None:
    """Re-sync every completed document from MongoDB to the vector DB."""
    logger.info("Starting full sync …")
    col = get_collection()
    total_videos = 0
    total_scenes = 0
    total_contents = 0

    for doc in col.find({"status": "completed"}):
        scenes = transform_mongo_doc(doc)
        if scenes:
            sync_upsert_scenes(scenes)
            total_scenes += len(scenes)
            total_videos += 1

        content = transform_mongo_doc_to_content(doc)
        if content:
            sync_upsert_content(content)
            total_contents += 1

    logger.info("Full sync done: %d videos, %d scenes, %d contents.",
                total_videos, total_scenes, total_contents)


# ---------------------------------------------------------------------------
# Change event handler
# ---------------------------------------------------------------------------

def _handle_change(change: dict) -> None:
    """Process a single change stream event."""
    op = change.get("operationType")
    doc_key = change.get("documentKey", {})
    doc_id = doc_key.get("_id")

    logger.info("Change event: op=%s, _id=%s", op, doc_id)

    if op in ("insert", "update", "replace"):
        full_doc = change.get("fullDocument")
        if full_doc is None:
            # fullDocument can be None if the doc was deleted between the
            # change and the lookup.  Fetch manually as a fallback.
            col = get_collection()
            full_doc = col.find_one({"_id": doc_id})

        if full_doc is None:
            logger.warning("Document %s not found — skipping.", doc_id)
            return

        if full_doc.get("status") != "completed":
            logger.debug("Skipping non-completed doc %s (status=%s).",
                         doc_id, full_doc.get("status"))
            return

        scenes = transform_mongo_doc(full_doc)
        if scenes:
            count = sync_upsert_scenes(scenes)
            logger.info("Upserted %d scenes for video %s.",
                        count, full_doc.get("unique_id", doc_id))
        else:
            logger.info("No scenes in doc %s — nothing to sync.", doc_id)

        content = transform_mongo_doc_to_content(full_doc)
        if content:
            sync_upsert_content(content)
            logger.info("Upserted content for video %s.",
                        full_doc.get("unique_id", doc_id))

    elif op == "delete":
        # Try to use pre-image if enabled (MongoDB changeStreamPreAndPostImages)
        pre_doc = change.get("fullDocumentBeforeChange")
        if pre_doc:
            scene_ids = get_scene_ids_from_doc(pre_doc)
            if scene_ids:
                deleted = sync_delete_scenes(scene_ids)
                logger.info("Deleted %d scenes for video %s.",
                            deleted, pre_doc.get("unique_id", doc_id))

            content_id = pre_doc.get("unique_id", str(pre_doc.get("_id", "")))
            if content_id:
                sync_delete_content(content_id)
                logger.info("Deleted content for video %s.", content_id)
        else:
            # Without pre-image we cannot recover scene_ids or content_id.
            # The CRUD API delete path should remove scenes/contents before
            # deleting the Mongo doc. Use /v1/videos/sync-all to reconcile.
            logger.warning(
                "Delete detected for _id=%s but no pre-image available. "
                "Scene/content cleanup is handled by the CRUD API; use "
                "POST /v1/videos/sync-all to reconcile if documents were "
                "deleted directly in MongoDB.", doc_id)

    else:
        logger.debug("Ignoring operationType=%s", op)


# ---------------------------------------------------------------------------
# Watch loop with reconnection
# ---------------------------------------------------------------------------

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info("Shutdown signal received (%s).  Stopping …", signum)
    _running = False


def watch_loop() -> None:
    """Main watch loop with exponential backoff on failure."""
    global _running

    backoff = 1  # seconds
    max_backoff = 60

    while _running:
        resume_token = _load_token()
        try:
            col = get_collection()
            watch_kwargs = {
                "full_document": "updateLookup",
            }
            if resume_token:
                watch_kwargs["resume_after"] = resume_token
                logger.info("Resuming from saved token.")

            pipeline = [
                {"$match": {
                    "operationType": {"$in": ["insert", "update", "replace", "delete"]}
                }}
            ]

            with col.watch(pipeline, **watch_kwargs) as stream:
                logger.info("Watching collection %s.%s …",
                            settings.mongo_db, settings.mongo_collection)
                backoff = 1  # reset on successful connection

                for change in stream:
                    if not _running:
                        break

                    try:
                        _handle_change(change)
                    except Exception:
                        logger.exception("Error handling change event:")

                    # Persist resume token after every event
                    token = stream.resume_token
                    if token:
                        _save_token(token)

        except PyMongoError as e:
            if not _running:
                break
            logger.error("MongoDB connection error: %s", e)
            logger.info("Reconnecting in %ds …", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

        except Exception:
            if not _running:
                break
            logger.exception("Unexpected error in watch loop:")
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

    logger.info("Watcher stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MongoDB → Vector DB sync watcher")
    parser.add_argument("--full-sync", action="store_true",
                        help="Run a full re-sync before starting the watcher")
    parser.add_argument("--full-sync-only", action="store_true",
                        help="Run a full re-sync and exit (don't watch)")
    parser.add_argument("--reset-token", action="store_true",
                        help="Clear the saved resume token and start fresh")
    args = parser.parse_args()

    # Register shutdown signals
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    if args.reset_token:
        _clear_token()

    # Test MongoDB connection
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        logger.info("MongoDB connected: %s", settings.mongo_uri)
    except Exception as e:
        logger.error("Cannot connect to MongoDB: %s", e)
        sys.exit(1)

    # Setup vector backend
    try:
        _ensure_backend()
    except Exception as e:
        logger.error("Vector backend setup failed: %s", e)
        sys.exit(1)

    if args.full_sync or args.full_sync_only:
        full_sync()
        if args.full_sync_only:
            return

    watch_loop()


if __name__ == "__main__":
    main()
