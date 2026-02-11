import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import crud, face_search, ingest, search
from src.config import settings

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def _setup_opensearch():
    from src.index_manager import ensure_index, ensure_ingest_pipeline, ensure_search_pipeline
    from src.opensearch_client import get_client

    client = get_client()
    ensure_ingest_pipeline(client)
    ensure_index(client)
    ensure_search_pipeline(client)
    logger.info("OpenSearch index and pipelines ready.")


def _setup_milvus():
    from src.milvus_client import get_embedding_fn, get_milvus_client
    from src.milvus_manager import ensure_collection

    client = get_milvus_client()
    ensure_collection(client)
    get_embedding_fn()  # pre-load model
    logger.info("Milvus collection and embedding model ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if settings.backend == "milvus":
            _setup_milvus()
        else:
            _setup_opensearch()
    except Exception as e:
        logger.warning(f"Backend setup skipped (will retry on first request): {e}")
    yield


app = FastAPI(
    title="Metadata Search API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(face_search.router)
# app.include_router(crud.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
