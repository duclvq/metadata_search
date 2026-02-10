# Metadata Search — API Reference

Base URL: `http://localhost:8000`

---

## GET /health

Health check.

**Response:** `{"status": "ok"}`

---

## POST /v1/scenes/ingest

Bulk ingest scenes with video metadata. OpenSearch auto-generates embeddings via ingest pipeline.

**Request:**
```json
{
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_description": "A car chase through the city streets",
      "start_time_sec": 120.0,
      "end_time_sec": 180.5,
      "video": {
        "video_id": "vid_abc",
        "video_title": "Action Movie Trailer",
        "video_description": "Official trailer for the action movie",
        "video_tags": ["action", "trailer"],
        "video_duration_sec": 300.0,
        "video_created_at": "2025-01-15T10:00:00Z"
      }
    }
  ]
}
```

**Response (200):**
```json
{
  "indexed": 1,
  "errors": []
}
```

**Notes:**
- `scene_id` is used as the document `_id` — re-ingesting the same `scene_id` overwrites the previous document.
- `video_description`, `video_tags`, `video_duration_sec`, `video_created_at` are optional.

---

## GET /v1/search/semantic

Pure vector (neural) search. OpenSearch converts the query text to an embedding using the pre-deployed model.

**Example:** `GET /v1/search/semantic?query_text=car+chase+scene&k=5`

**Response (200):**
```json
{
  "total": 5,
  "hits": [
    {
      "score": 0.92,
      "scene_id": "scene_001",
      "scene_description": "A car chase through the city streets",
      "start_time_sec": 120.0,
      "end_time_sec": 180.5,
      "video_id": "vid_abc",
      "video_title": "Action Movie Trailer",
      "video_description": "Official trailer for the action movie",
      "video_tags": ["action", "trailer"]
    }
  ]
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `query_text` | string | *(required)* | Search query |
| `k` | int | 10 | Number of results (1-100) |

---

## GET /v1/search/hybrid

Combined BM25 keyword search + neural vector search. Scores are normalized and merged (default: 30% BM25, 70% vector).

**Example:** `GET /v1/search/hybrid?query_text=car+chase+scene&k=10`

**Response:** Same format as semantic search.

| Field | Type | Default | Description |
|---|---|---|---|
| `query_text` | string | *(required)* | Search query (used for both BM25 and neural) |
| `k` | int | 10 | Number of results (1-100) |

**BM25 fields searched:** `scene_description` (boost 1.0), `video_title` (boost 1.5), `video_description` (boost 0.5).
