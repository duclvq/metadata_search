import logging

from pymilvus import (
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    MilvusClient,
)

from src.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def _build_scenes_schema() -> CollectionSchema:
    fields = [
        FieldSchema(name="scene_id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.embedding_dimension),
        # Scene-level fields
        FieldSchema(name="scene_description", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="start_time_sec", dtype=DataType.FLOAT),
        FieldSchema(name="end_time_sec", dtype=DataType.FLOAT),
        # Video-level fields (flattened)
        FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="video_title", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="video_description", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="video_tags", dtype=DataType.VARCHAR, max_length=4096),  # JSON-serialized list
        FieldSchema(name="video_duration_sec", dtype=DataType.FLOAT),
        FieldSchema(name="video_created_at", dtype=DataType.VARCHAR, max_length=64),
        # Scene metadata fields
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="created_date", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=256),
        # BM25 full-text search
        FieldSchema(
            name="bm25_text",
            dtype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            analyzer_params={"type": "standard"},
        ),
        FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
    ]
    schema = CollectionSchema(fields=fields, description="Video scene search collection")
    schema.add_function(Function(
        name="bm25",
        function_type=FunctionType.BM25,
        input_field_names=["bm25_text"],
        output_field_names=["sparse_embedding"],
    ))
    return schema


def _build_contents_schema() -> CollectionSchema:
    fields = [
        FieldSchema(name="content_id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.embedding_dimension),
        # Content-level fields
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=4096),  # JSON-serialized list
        FieldSchema(name="duration_sec", dtype=DataType.FLOAT),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=256),
        # BM25 full-text search
        FieldSchema(
            name="bm25_text",
            dtype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            analyzer_params={"type": "standard"},
        ),
        FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
    ]
    schema = CollectionSchema(fields=fields, description="Whole-video content search collection")
    schema.add_function(Function(
        name="bm25",
        function_type=FunctionType.BM25,
        input_field_names=["bm25_text"],
        output_field_names=["sparse_embedding"],
    ))
    return schema


# ---------------------------------------------------------------------------
# Schema compatibility check
# ---------------------------------------------------------------------------

def _schema_compatible(client: MilvusClient, collection: str, required_fields: set[str]) -> bool:
    """Check if existing collection has the expected fields."""
    try:
        info = client.describe_collection(collection_name=collection)
        field_names = {f["name"] for f in info.get("fields", [])}
        return required_fields.issubset(field_names)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Ensure collections
# ---------------------------------------------------------------------------

def _ensure_single_collection(
    client: MilvusClient,
    collection_name: str,
    schema_builder,
    required_fields: set[str],
) -> None:
    if client.has_collection(collection_name=collection_name):
        if not _schema_compatible(client, collection_name, required_fields):
            logger.warning(
                "Collection '%s' exists but has incompatible schema. "
                "Run 'python -m scripts.drop_collection' to drop and recreate it.",
                collection_name,
            )
        client.load_collection(collection_name=collection_name)
        return

    schema = schema_builder()
    client.create_collection(collection_name=collection_name, schema=schema)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 128},
    )
    index_params.add_index(
        field_name="sparse_embedding",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )
    client.create_index(collection_name=collection_name, index_params=index_params)
    client.load_collection(collection_name=collection_name)


def ensure_collection(client: MilvusClient) -> None:
    """Ensure both scenes and contents collections exist."""
    _ensure_single_collection(
        client,
        settings.milvus_collection_name,
        _build_scenes_schema,
        {"scene_id", "category", "created_date", "author", "bm25_text", "sparse_embedding"},
    )
    _ensure_single_collection(
        client,
        settings.milvus_content_collection_name,
        _build_contents_schema,
        {"content_id", "title", "description", "bm25_text", "sparse_embedding"},
    )
