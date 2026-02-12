# Metadata Search - Project Overview

## 📋 Tổng quan dự án

Hệ thống tìm kiếm video/scene thông minh sử dụng vector database (Milvus/OpenSearch) với khả năng semantic search, full-text search và hybrid search.

### Scope dự án

1. **Indexing & Sync**: Đồng bộ dữ liệu video/scene từ MongoDB sang vector DB
2. **Search APIs**: Cung cấp 7 API search với nhiều phương thức tìm kiếm
3. **Face Search**: Tìm kiếm scene theo khuôn mặt
4. **Metadata Filtering**: Lọc kết quả theo category, author, date...

---

## 🔄 Luồng xử lý dữ liệu

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   MongoDB   │  ────>  │  Sync/Ingest │  ────>  │  Vector DB  │
│ (video_queue)│         │    Service   │         │(Milvus/OS)  │
└─────────────┘         └──────────────┘         └─────────────┘
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │  Search APIs │
                                                   └──────────────┘
```

### Các bước xử lý

1. **Data Enrichment**: Video được xử lý AI (scene detection, transcript, face recognition)
2. **Storage**: Lưu vào MongoDB collection `video_queue`
3. **Sync**: Script/API đồng bộ sang vector DB với embedding
4. **Search**: Client query qua FastAPI → Vector DB → trả kết quả ranked

---

## 📁 Cấu trúc thư mục

```
metadata_search/
│
├── api/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── models/                   # Pydantic models
│   │   ├── search.py            # Search response models
│   │   └── scene.py             # Ingest request models
│   ├── routes/                   # API endpoints
│   │   ├── search.py            # Scene & Content search
│   │   ├── face_search.py       # Face search
│   │   ├── ingest.py            # Ingest scenes/contents
│   │   └── crud.py              # CRUD MongoDB (disabled)
│   └── static/                   # Frontend files
│
├── src/                          # Core business logic
│   ├── config.py                # Configuration (env vars)
│   ├── milvus_client.py         # Milvus connection
│   ├── milvus_manager.py        # Milvus collection setup
│   ├── milvus_queries.py        # Milvus search queries
│   ├── opensearch_client.py     # OpenSearch connection
│   ├── index_manager.py         # OpenSearch index setup
│   ├── queries.py               # OpenSearch queries
│   ├── mongo_client.py          # MongoDB connection
│   └── sync_utils.py            # MongoDB → Vector DB sync
│
├── scripts/                      # Utility scripts
│   ├── ingest_data.py           # Manual data ingest
│   ├── mongo_watcher.py         # Watch MongoDB changes
│   └── drop_collection.py       # Drop Milvus collection
│
├── tests/                        # Unit tests
│   ├── conftest.py              # Pytest fixtures
│   ├── test_health.py           # Health check tests
│   ├── test_models.py           # Model validation tests
│   ├── test_ingest.py           # Ingest endpoint tests
│   └── test_search_formats.py   # Search format tests
│
├── format/                       # 📄 JSON format definitions
│   ├── mongodb_schema.json      # MongoDB video_queue schema
│   ├── scene_ingest.json        # Scene ingest request format
│   ├── content_ingest.json      # Content ingest request format
│   ├── scene_search_response.json    # Scene search output
│   ├── content_search_response.json  # Content search output
│   └── face_search_response.json     # Face search output
│
├── dockers/                      # Docker configs
│   ├── milvus/
│   ├── open_search/
│   ├── search_api/
│   └── sync_service/
│
├── notebook/                     # Jupyter notebooks (demos)
├── example_data/                 # Sample data
├── evaluation/                   # Evaluation scripts
│
├── api_search_output_formats.md  # API output documentation
├── api_docs.md                   # API documentation
├── api_guide.md                  # API usage guide
├── spec.md                       # Technical specification
├── README.md                     # Getting started
├── requirements.txt              # Python dependencies
└── requirements-test.txt         # Test dependencies
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI 0.1+ |
| **Vector DB** | Milvus 2.6+ hoặc OpenSearch 2.10+ |
| **Source DB** | MongoDB 6+ (replica set) |
| **Embedding Model** | BAAI/bge-m3 (1024 dims) |
| **Language** | Python 3.11+ |
| **Testing** | Pytest + httpx |
| **Deployment** | Docker Compose |

---

## 🎯 Main Features

### 1. Search APIs (7 endpoints)
- Scene search: semantic, fulltext, hybrid
- Content search: semantic, fulltext, hybrid  
- Face search: tìm theo khuôn mặt
- Filtering: category, author, date, program...

### 2. Data Sync
- Manual ingest qua API
- Auto-sync từ MongoDB change stream
- Bulk sync toàn bộ dữ liệu

### 3. Dual Backend Support
- **Milvus**: Full features (semantic + fulltext + hybrid)
- **OpenSearch**: Semantic + hybrid only

### 4. Rich Metadata
- Scene-level: description, caption, audio, faces, timestamps
- Video-level: title, tags, duration, resolution, fps
- Classification: category, author, program, broadcast date

---

## 📊 API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/search/scene` | GET | Tìm scene theo text |
| `/v1/search/scene/filter` | POST | Tìm scene + filter |
| `/v1/search/content` | GET | Tìm video/content |
| `/v1/search/content/filter` | POST | Tìm content + filter |
| `/v1/face_search` | POST | Tìm scene theo face |
| `/v1/face_search/filter` | POST | Tìm face + filter |
| `/v1/search/scene/list` | GET | List tất cả scenes |
| `/v1/scenes/ingest` | POST | Index scenes |
| `/v1/contents/ingest` | POST | Index contents |
| `/health` | GET | Health check |

Chi tiết: [api_search_output_formats.md](api_search_output_formats.md)

---

## 🚀 Quick Start

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Cấu hình .env
cp .env.example .env
# Edit MS_BACKEND, MS_MONGO_URI, MS_MILVUS_URI...

# 3. Khởi động MongoDB replica set
mongosh --eval "rs.initiate()"

# 4. Start API
uvicorn api.main:app --reload --port 8000

# 5. Test
curl http://localhost:8000/health
```

---

## 📝 Documentation Files

| File | Description |
|------|-------------|
| [README.md](README.md) | Getting started guide |
| [spec.md](spec.md) | Technical specification |
| [api_docs.md](api_docs.md) | API documentation |
| [api_guide.md](api_guide.md) | API usage guide |
| [api_search_output_formats.md](api_search_output_formats.md) | Search API output formats |
| [tests/README.md](tests/README.md) | Testing guide |
| **PROJECT_OVERVIEW.md** | 📍 This file |

---

## 📦 Data Format Files

Folder `format/` chứa các định dạng JSON chuẩn:

1. **Input Formats** (từ MongoDB/Client → System)
   - `mongodb_schema.json` - Schema MongoDB video_queue collection
   - `scene_ingest.json` - Request body cho `/v1/scenes/ingest`
   - `content_ingest.json` - Request body cho `/v1/contents/ingest`

2. **Output Formats** (từ System → Client)
   - `scene_search_response.json` - Response của scene search APIs
   - `content_search_response.json` - Response của content search APIs
   - `face_search_response.json` - Response của face search APIs
   - `scene_list_response.json` - Response của scene list API

3. **Internal Formats** (giữa các components)
   - `milvus_scene_schema.json` - Schema collection scenes trong Milvus
   - `milvus_content_schema.json` - Schema collection contents trong Milvus
   - `opensearch_index_mapping.json` - Mapping của OpenSearch index

Xem chi tiết: [format/README.md](format/README.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=api --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

Chi tiết: [tests/README.md](tests/README.md)

---

## 🐳 Docker Deployment

```bash
# Start Milvus
cd dockers/milvus && docker-compose up -d

# Start OpenSearch  
cd dockers/open_search && docker-compose up -d

# Start API
cd dockers/search_api && docker-compose up -d
```

---

## 📞 Support

- **Issues**: GitHub Issues
- **Docs**: Xem các file .md trong project
- **Tests**: `pytest tests/ -v` để kiểm tra format
