import json
from collections import defaultdict

from pymilvus import AnnSearchRequest, MilvusClient, RRFRanker

from src.config import settings

# ---------------------------------------------------------------------------
# Scene output fields & helpers
# ---------------------------------------------------------------------------

SCENE_OUTPUT_FIELDS = [
    "scene_id",
    "scene_description",
    "start_time_sec",
    "end_time_sec",
    "video_id",
    "video_title",
    "video_description",
    "video_tags",
    "video_duration_sec",
    "video_created_at",
    "category",
    "created_date",
    "author",
]

SCENE_FACET_FIELDS = ["category", "created_date", "author"]


def _parse_scene_hit(result: dict) -> dict:
    entity = result["entity"]
    tags = entity.get("video_tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = []

    return {
        "score": result["distance"],
        "scene_id": entity.get("scene_id", ""),
        "scene_description": entity.get("scene_description", ""),
        "start_time_sec": entity.get("start_time_sec", 0.0),
        "end_time_sec": entity.get("end_time_sec", 0.0),
        "video_id": entity.get("video_id", ""),
        "video_title": entity.get("video_title", ""),
        "video_description": entity.get("video_description"),
        "video_tags": tags,
        "category": entity.get("category", ""),
        "created_date": entity.get("created_date", ""),
        "author": entity.get("author", ""),
    }


def build_scene_facets(hits: list[dict]) -> dict:
    groups = {field: defaultdict(list) for field in SCENE_FACET_FIELDS}
    for hit in hits:
        for field in SCENE_FACET_FIELDS:
            value = hit.get(field, "")
            if value:
                groups[field][value].append(hit["scene_id"])

    facets = {}
    for field in SCENE_FACET_FIELDS:
        facets[field] = [
            {"value": value, "count": len(ids), "scene_ids": ids}
            for value, ids in sorted(groups[field].items(), key=lambda x: -len(x[1]))
        ]
    return facets


# ---------------------------------------------------------------------------
# Content output fields & helpers
# ---------------------------------------------------------------------------

CONTENT_OUTPUT_FIELDS = [
    "content_id",
    "title",
    "description",
    "tags",
    "duration_sec",
    "created_at",
    "category",
    "author",
]

CONTENT_FACET_FIELDS = ["category", "author"]


def _parse_content_hit(result: dict) -> dict:
    entity = result["entity"]
    tags = entity.get("tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = []

    return {
        "score": result["distance"],
        "content_id": entity.get("content_id", ""),
        "title": entity.get("title", ""),
        "description": entity.get("description", ""),
        "tags": tags,
        "duration_sec": entity.get("duration_sec", 0.0),
        "created_at": entity.get("created_at", ""),
        "category": entity.get("category", ""),
        "author": entity.get("author", ""),
    }


def build_content_facets(hits: list[dict]) -> dict:
    groups = {field: defaultdict(list) for field in CONTENT_FACET_FIELDS}
    for hit in hits:
        for field in CONTENT_FACET_FIELDS:
            value = hit.get(field, "")
            if value:
                groups[field][value].append(hit["content_id"])

    facets = {}
    for field in CONTENT_FACET_FIELDS:
        facets[field] = [
            {"value": value, "count": len(ids), "content_ids": ids}
            for value, ids in sorted(groups[field].items(), key=lambda x: -len(x[1]))
        ]
    return facets


# ---------------------------------------------------------------------------
# Scene search functions
# ---------------------------------------------------------------------------

def search_scene_semantic(
    client: MilvusClient,
    embedding_fn,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    query_vectors = embedding_fn.encode_queries([query_text])

    search_kwargs = {
        "collection_name": settings.milvus_collection_name,
        "data": query_vectors,
        "anns_field": "embedding",
        "limit": k,
        "output_fields": SCENE_OUTPUT_FIELDS,
        "search_params": {"metric_type": "COSINE", "params": {"ef": 256}},
    }
    if filter_expr:
        search_kwargs["filter"] = filter_expr

    results = client.search(**search_kwargs)
    hits = [_parse_scene_hit(r) for r in results[0]]
    facets = build_scene_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}


def search_scene_fulltext(
    client: MilvusClient,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    search_kwargs = {
        "collection_name": settings.milvus_collection_name,
        "data": [query_text],
        "anns_field": "sparse_embedding",
        "limit": k,
        "output_fields": SCENE_OUTPUT_FIELDS,
        "search_params": {"metric_type": "BM25"},
    }
    if filter_expr:
        search_kwargs["filter"] = filter_expr

    results = client.search(**search_kwargs)
    hits = [_parse_scene_hit(r) for r in results[0]]
    facets = build_scene_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}


def search_scene_fulltext_with_filter(
    client: MilvusClient,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    """Alias for search_scene_fulltext with filter support."""
    return search_scene_fulltext(client, query_text, k, filter_expr)


def search_scene_hybrid(
    client: MilvusClient,
    embedding_fn,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    query_vectors = embedding_fn.encode_queries([query_text])

    dense_req = AnnSearchRequest(
        data=query_vectors,
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 256}},
        limit=k,
    )
    sparse_req = AnnSearchRequest(
        data=[query_text],
        anns_field="sparse_embedding",
        param={"metric_type": "BM25"},
        limit=k,
    )

    hybrid_kwargs = {
        "collection_name": settings.milvus_collection_name,
        "reqs": [dense_req, sparse_req],
        "ranker": RRFRanker(k=60),
        "limit": k,
        "output_fields": SCENE_OUTPUT_FIELDS,
    }
    if filter_expr:
        hybrid_kwargs["filter"] = filter_expr

    results = client.hybrid_search(**hybrid_kwargs)
    hits = [_parse_scene_hit(r) for r in results[0]]
    facets = build_scene_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}


# ---------------------------------------------------------------------------
# Content search functions
# ---------------------------------------------------------------------------

def search_content_semantic(
    client: MilvusClient,
    embedding_fn,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    query_vectors = embedding_fn.encode_queries([query_text])

    search_kwargs = {
        "collection_name": settings.milvus_content_collection_name,
        "data": query_vectors,
        "anns_field": "embedding",
        "limit": k,
        "output_fields": CONTENT_OUTPUT_FIELDS,
        "search_params": {"metric_type": "COSINE", "params": {"ef": 256}},
    }
    if filter_expr:
        search_kwargs["filter"] = filter_expr

    results = client.search(**search_kwargs)
    hits = [_parse_content_hit(r) for r in results[0]]
    facets = build_content_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}


def search_content_fulltext(
    client: MilvusClient,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    search_kwargs = {
        "collection_name": settings.milvus_content_collection_name,
        "data": [query_text],
        "anns_field": "sparse_embedding",
        "limit": k,
        "output_fields": CONTENT_OUTPUT_FIELDS,
        "search_params": {"metric_type": "BM25"},
    }
    if filter_expr:
        search_kwargs["filter"] = filter_expr

    results = client.search(**search_kwargs)
    hits = [_parse_content_hit(r) for r in results[0]]
    facets = build_content_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}


def search_content_hybrid(
    client: MilvusClient,
    embedding_fn,
    query_text: str,
    k: int,
    filter_expr: str | None = None,
) -> dict:
    query_vectors = embedding_fn.encode_queries([query_text])

    dense_req = AnnSearchRequest(
        data=query_vectors,
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 256}},
        limit=k,
    )
    sparse_req = AnnSearchRequest(
        data=[query_text],
        anns_field="sparse_embedding",
        param={"metric_type": "BM25"},
        limit=k,
    )

    hybrid_kwargs = {
        "collection_name": settings.milvus_content_collection_name,
        "reqs": [dense_req, sparse_req],
        "ranker": RRFRanker(k=60),
        "limit": k,
        "output_fields": CONTENT_OUTPUT_FIELDS,
    }
    if filter_expr:
        hybrid_kwargs["filter"] = filter_expr

    results = client.hybrid_search(**hybrid_kwargs)
    hits = [_parse_content_hit(r) for r in results[0]]
    facets = build_content_facets(hits)
    return {"total": len(hits), "hits": hits, "facets": facets}
