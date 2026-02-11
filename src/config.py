from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend: str = "opensearch"  # "opensearch" or "milvus"

    # --- OpenSearch settings ---
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_scheme: str = "http"
    opensearch_user: str = "admin"
    opensearch_password: str = "YourStrongPassword123!"
    opensearch_verify_certs: bool = False

    index_name: str = "scenes"
    embedding_dimension: int = 768
    model_id: str = ""  # Required for OpenSearch backend

    search_pipeline_name: str = "hybrid-search-pipeline"
    ingest_pipeline_name: str = "scene-embedding-pipeline"

    # --- MongoDB settings ---
    # mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_uri: str = "mongodb://host.docker.internal:27017/?replicaSet=rs0"
    mongo_db: str = "Metadata_Enrichment"
    mongo_collection: str = "video_queue"
    mongo_resume_token_path: str = "resume_token.json"

    # --- Milvus settings ---
    milvus_uri: str = "http://localhost:19530"
    milvus_collection_name: str = "scenes"
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"

    model_config = {"env_prefix": "MS_", "env_file": ".env"}


settings = Settings()
