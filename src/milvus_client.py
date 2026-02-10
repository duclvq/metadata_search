from pymilvus import MilvusClient
from pymilvus import model

from src.config import settings

_client: MilvusClient | None = None
_embedding_fn = None


def get_milvus_client() -> MilvusClient:
    global _client
    if _client is None:
        _client = MilvusClient(settings.milvus_uri)
    return _client


def get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model_name,
            device=settings.embedding_device,
        )
    return _embedding_fn
