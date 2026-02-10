from src.config import settings


def build_semantic_query(query_text: str, k: int) -> dict:
    """Pure neural (k-NN) query — OpenSearch converts text to embedding."""
    return {
        "size": k,
        "query": {
            "neural": {
                "embedding": {
                    "query_text": query_text,
                    "model_id": settings.model_id,
                    "k": k,
                }
            }
        },
    }


def build_hybrid_query(query_text: str, k: int) -> dict:
    """Hybrid query: BM25 keyword search + neural vector search."""
    return {
        "size": k,
        "query": {
            "hybrid": {
                "queries": [
                    {
                        "bool": {
                            "should": [
                                {"match": {"scene_description": {"query": query_text}}},
                                {"match": {"video_title": {"query": query_text, "boost": 1.5}}},
                                {"match": {"video_description": {"query": query_text, "boost": 0.5}}},
                            ]
                        }
                    },
                    {
                        "neural": {
                            "embedding": {
                                "query_text": query_text,
                                "model_id": settings.model_id,
                                "k": k,
                            }
                        }
                    },
                ]
            }
        },
    }
