import json
from collections import defaultdict

from pymilvus import MilvusClient

from src.config import settings

OUTPUT_FIELDS = [
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

FACET_FIELDS = ["category", "created_date", "author"]


def _parse_hit(result: dict) -> dict:
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


def build_facets(hits: list[dict]) -> dict:
    """Group hits by category, created_date, author using defaultdict (fastest for <1K items)."""
    groups = {field: defaultdict(list) for field in FACET_FIELDS}

    for hit in hits:
        for field in FACET_FIELDS:
            value = hit.get(field, "")
            if value:
                groups[field][value].append(hit["scene_id"])

    facets = {}
    for field in FACET_FIELDS:
        facets[field] = [
            {"value": value, "count": len(ids), "scene_ids": ids}
            for value, ids in sorted(groups[field].items(), key=lambda x: -len(x[1]))
        ]

    return facets


def search_semantic(
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
        "limit": k,
        "output_fields": OUTPUT_FIELDS,
        "search_params": {"metric_type": "COSINE", "params": {"ef": 256}},
    }
    if filter_expr:
        search_kwargs["filter"] = filter_expr

    results = client.search(**search_kwargs)

    hits = [_parse_hit(r) for r in results[0]]
    facets = build_facets(hits)

    return {"total": len(hits), "hits": hits, "facets": facets}
