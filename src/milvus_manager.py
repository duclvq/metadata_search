from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient

from src.config import settings


def _build_schema() -> CollectionSchema:
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
        FieldSchema(name="video_created_at", dtype=DataType.VARCHAR, max_length=64),  # ISO format string
        # Scene metadata fields
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="created_date", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=256),
    ]
    return CollectionSchema(fields=fields, description="Video scene search collection")


def _schema_compatible(client: MilvusClient, collection: str) -> bool:
    """Check if existing collection has our expected schema (scene_id as primary key)."""
    try:
        info = client.describe_collection(collection_name=collection)
        field_names = {f["name"] for f in info.get("fields", [])}
        required = {"scene_id", "category", "created_date", "author"}
        return required.issubset(field_names)
    except Exception:
        return False


def ensure_collection(client: MilvusClient) -> None:
    collection = settings.milvus_collection_name

    if client.has_collection(collection_name=collection):
        if not _schema_compatible(client, collection):
            # Schema mismatch (e.g. old collection with auto 'id' field) — drop and recreate
            client.drop_collection(collection_name=collection)

    if not client.has_collection(collection_name=collection):
        schema = _build_schema()
        client.create_collection(
            collection_name=collection,
            schema=schema,
        )

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 128},
        )
        client.create_index(
            collection_name=collection,
            index_params=index_params,
        )

    # Always load — required after Milvus restart even if collection exists
    client.load_collection(collection_name=collection)
