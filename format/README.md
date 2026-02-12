# Data Format Definitions

Thư mục này chứa các định dạng JSON chuẩn cho toàn bộ hệ thống.

## 📊 Tổng quan

| File | Loại | Mô tả |
|------|------|-------|
| `mongodb_schema.json` | Input | Schema MongoDB collection `video_queue` |
| `scene_ingest.json` | Input | Request format cho POST `/v1/scenes/ingest` |
| `content_ingest.json` | Input | Request format cho POST `/v1/contents/ingest` |
| `scene_search_response.json` | Output | Response format của scene search APIs |
| `content_search_response.json` | Output | Response format của content search APIs |
| `face_search_response.json` | Output | Response format của face search APIs |
| `scene_list_response.json` | Output | Response format của scene list API |
| `milvus_scene_schema.json` | Internal | Milvus collection schema cho scenes |
| `milvus_content_schema.json` | Internal | Milvus collection schema cho contents |
| `opensearch_index_mapping.json` | Internal | OpenSearch index mapping |

---

## 🔄 Luồng dữ liệu

```
MongoDB (mongodb_schema.json)
    │
    ├─> Sync Service
    │       │
    │       ├─> Milvus (milvus_scene_schema.json)
    │       └─> OpenSearch (opensearch_index_mapping.json)
    │
    └─> FastAPI Ingest
            ├─> scene_ingest.json
            └─> content_ingest.json
```

```
Client Request
    │
    ├─> Search APIs
    │       ├─> scene_search_response.json
    │       ├─> content_search_response.json
    │       └─> face_search_response.json
    │
    └─> List API
            └─> scene_list_response.json
```

---

## 📥 Input Formats

### 1. MongoDB Schema (`mongodb_schema.json`)

Document từ MongoDB collection `video_queue` sau khi được enrichment:

```json
{
  "_id": "ObjectId",
  "unique_id": "video_001",
  "status": "completed",
  "video_path": "/path/to/video.mp4",
  "enriched_data": {
    "video_metadata": { ... },
    "scenes": [ ... ],
    "faces": [ ... ]
  }
}
```

**Được dùng bởi:**
- `sync_utils.py` - Transform sang vector DB
- `mongo_watcher.py` - Watch changes
- `crud.py` - CRUD operations

---

### 2. Scene Ingest Format (`scene_ingest.json`)

Request body cho `POST /v1/scenes/ingest`:

```json
{
  "scenes": [
    {
      "scene_id": "video001_scene_001",
      "scene_description": "Hai người đang họp",
      "visual_caption": "Two people in meeting",
      "audio_summarization": "Thảo luận kế hoạch",
      "audio_transcription": "Chúng ta cần...",
      "faces": [
        {"face_id": "f001", "name": "Nguyen Van A"}
      ],
      "start_time_sec": 10.5,
      "end_time_sec": 25.3,
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe",
      "video": {
        "video_id": "video001",
        "video_title": "Họp team",
        "video_name": "meeting.mp4",
        "video_summary": "Cuộc họp team",
        "video_tags": ["meeting", "business"],
        "video_duration_sec": 3600.0,
        "video_created_at": "2026-01-15T10:30:00",
        "resolution": "1920x1080",
        "fps": 30.0,
        "program_id": "prog_001",
        "broadcast_date": "2026-01-20",
        "content_type_id": "internal"
      }
    }
  ]
}
```

**Được validate bởi:**
- `api/models/scene.py::IngestRequest`
- `tests/test_ingest.py`

---

### 3. Content Ingest Format (`content_ingest.json`)

Request body cho `POST /v1/contents/ingest`:

```json
{
  "contents": [
    {
      "content_id": "video001",
      "title": "Họp team marketing",
      "description": "Cuộc họp về kế hoạch Q1",
      "video_summary": "Thảo luận marketing",
      "tags": ["meeting", "marketing"],
      "duration_sec": 3600.0,
      "created_at": "2026-01-15T10:30:00",
      "category": "business",
      "author": "John Doe",
      "video_name": "meeting.mp4",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal"
    }
  ]
}
```

**Được validate bởi:**
- `api/models/scene.py::ContentIngestRequest`
- `tests/test_ingest.py`

---

## 📤 Output Formats

### 4. Scene Search Response (`scene_search_response.json`)

Response của:
- `GET /v1/search/scene`
- `POST /v1/search/scene/filter`
- `POST /v1/face_search`
- `POST /v1/face_search/filter`

```json
{
  "total": 42,
  "hits": [
    {
      "score": 0.856,
      "scene_id": "video001_scene_001",
      "scene_description": "Hai người đang họp",
      "visual_caption": "Two people in meeting",
      "audio_summarization": "Thảo luận kế hoạch",
      "audio_transcription": "Chúng ta cần...",
      "faces": [
        {"face_id": "f001", "name": "Nguyen Van A"}
      ],
      "start_time_sec": 10.5,
      "end_time_sec": 25.3,
      "content_id": "video001",
      "video_title": "Họp team",
      "video_name": "meeting.mp4",
      "video_summary": "Cuộc họp team",
      "video_tags": ["meeting"],
      "video_duration_sec": 3600.0,
      "video_created_at": "2026-01-15T10:30:00",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal",
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe"
    }
  ],
  "facets": {
    "category": [
      {"value": "business", "count": 25, "scene_ids": ["s1", "s2"]}
    ],
    "created_date": [],
    "author": [],
    "broadcast_date": [],
    "program_id": [],
    "content_type_id": []
  }
}
```

**Được define bởi:**
- `api/models/search.py::SearchResponse`
- Được test bởi `tests/test_search_formats.py`

---

### 5. Content Search Response (`content_search_response.json`)

Response của:
- `GET /v1/search/content`
- `POST /v1/search/content/filter`

```json
{
  "total": 15,
  "hits": [
    {
      "score": 0.923,
      "content_id": "video001",
      "title": "Họp team marketing",
      "description": "Cuộc họp Q1",
      "video_summary": "Thảo luận marketing",
      "tags": ["meeting", "marketing"],
      "duration_sec": 3600.0,
      "created_at": "2026-01-15T10:30:00",
      "category": "business",
      "author": "John Doe",
      "video_name": "meeting.mp4",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal"
    }
  ],
  "facets": {
    "category": [
      {"value": "business", "count": 8, "content_ids": ["v1", "v2"]}
    ],
    "author": [],
    "broadcast_date": [],
    "program_id": [],
    "content_type_id": []
  }
}
```

**Được define bởi:**
- `api/models/search.py::ContentSearchResponse`

---

### 6. Face Search Response (`face_search_response.json`)

Response của face search APIs (cấu trúc giống Scene Search Response):

```json
{
  "total": 8,
  "hits": [ /* SceneHit[] */ ],
  "facets": { /* Facets */ }
}
```

**Lưu ý:** Face search trả về scenes chứa khuôn mặt được tìm.

---

### 7. Scene List Response (`scene_list_response.json`)

Response của `GET /v1/search/scene/list`:

```json
{
  "total": 150,
  "items": [
    {
      "scene_id": "video001_scene_001",
      "scene_description": "...",
      "visual_caption": "...",
      "audio_summarization": "...",
      "audio_transcription": "...",
      "faces": [],
      "start_time_sec": 10.5,
      "end_time_sec": 25.3,
      "content_id": "video001",
      "video_title": "...",
      "video_name": "...",
      "video_summary": "...",
      "video_tags": [],
      "video_duration_sec": 3600.0,
      "video_created_at": "2026-01-15T10:30:00",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal",
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe"
    }
  ]
}
```

**Khác biệt với Search Response:**
- Không có `score` field
- Không có `facets`
- Dùng `items` thay vì `hits`

---

## 🔧 Internal Formats

### 8. Milvus Scene Schema (`milvus_scene_schema.json`)

Schema của collection `scenes` trong Milvus:

```json
{
  "collection_name": "scenes",
  "fields": [
    {"name": "scene_id", "type": "VARCHAR", "is_primary": true, "max_length": 255},
    {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1024},
    {"name": "scene_description", "type": "VARCHAR", "max_length": 65535},
    {"name": "visual_caption", "type": "VARCHAR", "max_length": 65535},
    {"name": "audio_summarization", "type": "VARCHAR", "max_length": 65535},
    {"name": "audio_transcription", "type": "VARCHAR", "max_length": 65535},
    {"name": "faces", "type": "VARCHAR", "max_length": 65535},
    {"name": "start_time_sec", "type": "FLOAT"},
    {"name": "end_time_sec", "type": "FLOAT"},
    {"name": "video_id", "type": "VARCHAR", "max_length": 255},
    {"name": "video_title", "type": "VARCHAR", "max_length": 1024},
    {"name": "bm25_text", "type": "VARCHAR", "max_length": 65535, "enable_analyzer": true}
  ],
  "indexes": [
    {"field": "embedding", "type": "HNSW", "metric": "COSINE"},
    {"field": "bm25_text", "type": "BM25"}
  ]
}
```

**Được dùng bởi:**
- `src/milvus_manager.py::ensure_collection()`

---

### 9. Milvus Content Schema (`milvus_content_schema.json`)

Schema của collection `contents` trong Milvus:

```json
{
  "collection_name": "contents",
  "fields": [
    {"name": "content_id", "type": "VARCHAR", "is_primary": true, "max_length": 255},
    {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1024},
    {"name": "title", "type": "VARCHAR", "max_length": 1024},
    {"name": "description", "type": "VARCHAR", "max_length": 65535},
    {"name": "tags", "type": "VARCHAR", "max_length": 65535},
    {"name": "bm25_text", "type": "VARCHAR", "max_length": 65535, "enable_analyzer": true}
  ],
  "indexes": [
    {"field": "embedding", "type": "HNSW", "metric": "COSINE"},
    {"field": "bm25_text", "type": "BM25"}
  ]
}
```

---

### 10. OpenSearch Index Mapping (`opensearch_index_mapping.json`)

Mapping của OpenSearch index `scenes`:

```json
{
  "mappings": {
    "properties": {
      "scene_id": {"type": "keyword"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "engine": "lucene",
          "space_type": "cosinesimil"
        }
      },
      "scene_description": {"type": "text"},
      "video_title": {"type": "text"},
      "start_time_sec": {"type": "float"},
      "end_time_sec": {"type": "float"}
    }
  }
}
```

**Được dùng bởi:**
- `src/index_manager.py::ensure_index()`

---

## ✅ Validation

Tất cả formats được validate qua:

1. **Pydantic Models** (`api/models/`)
2. **Unit Tests** (`tests/test_models.py`, `tests/test_ingest.py`)
3. **API Tests** (`tests/test_search_formats.py`)

Run tests:
```bash
pytest tests/test_models.py -v
pytest tests/test_ingest.py -v
pytest tests/test_search_formats.py -v
```

---

## 📚 Related Documentation

- [api_search_output_formats.md](../api_search_output_formats.md) - Chi tiết output formats
- [api_docs.md](../api_docs.md) - API documentation
- [tests/README.md](../tests/README.md) - Testing guide
- [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) - Project overview
