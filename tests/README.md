# Unit Tests for Metadata Search API

## Tổng quan

Bộ test này kiểm tra:
1. **Health check** - Endpoint health
2. **Model validation** - Validate format định nghĩa trong API
3. **Ingest endpoints** - Test scene và content ingest
4. **Search formats** - Validate cấu trúc response của các search API

## Cài đặt

```bash
pip install pytest pytest-cov httpx
```

## Chạy tests

### Chạy tất cả tests

```bash
pytest tests/ -v
```

### Chạy test cụ thể

```bash
# Test health check
pytest tests/test_health.py -v

# Test model validation
pytest tests/test_models.py -v

# Test ingest
pytest tests/test_ingest.py -v

# Test search formats
pytest tests/test_search_formats.py -v
```

### Chạy với coverage

```bash
pytest tests/ --cov=api --cov=src --cov-report=html
```

### Chạy tests với output chi tiết

```bash
pytest tests/ -v -s
```

## Cấu trúc tests

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures và configuration
├── test_health.py           # Health check tests
├── test_models.py           # Model validation tests
├── test_ingest.py           # Ingest endpoint tests
├── test_search_formats.py   # Search API format tests
└── README.md                # Documentation này
```

## Test Cases

### 1. Health Check (`test_health.py`)
- ✅ Test endpoint `/health` trả về `{"status": "ok"}`
- ✅ Validate response format

### 2. Model Validation (`test_models.py`)
- ✅ Test `SceneHit`, `ContentHit` models
- ✅ Test `FaceItem`, `Facets` structures
- ✅ Test `SearchResponse`, `ContentSearchResponse`
- ✅ Test `IngestRequest`, `IngestResponse`
- ✅ Test optional/required fields
- ✅ Test validation errors

### 3. Ingest Endpoints (`test_ingest.py`)
- ✅ Test `POST /v1/scenes/ingest`
- ✅ Test `POST /v1/contents/ingest`
- ✅ Validate request format
- ✅ Validate response structure
- ✅ Test validation errors
- ✅ Test missing required fields

### 4. Search Formats (`test_search_formats.py`)
- ✅ Test `GET /v1/search/scene`
- ✅ Test `POST /v1/search/scene/filter`
- ✅ Test `GET /v1/search/content`
- ✅ Test `POST /v1/search/content/filter`
- ✅ Test `GET /v1/search/scene/list`
- ✅ Test `POST /v1/face_search`
- ✅ Test `POST /v1/face_search/filter`
- ✅ Validate response structures
- ✅ Validate facets format

## Lưu ý

### Backend dependency
- Một số tests có thể fail nếu backend (Milvus/OpenSearch) chưa được setup
- Tests được thiết kế để gracefully handle khi backend không available
- Response codes được check: `200` (success), `502` (backend error), `501` (not implemented)

### Test data
- Sample data được define trong `conftest.py`
- Có thể modify để test với data khác

### CI/CD Integration
Tests có thể chạy trong CI/CD pipeline:
```yaml
- name: Run tests
  run: pytest tests/ -v --cov=api --cov=src
```

## Ví dụ output

```
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_health_check_response_format PASSED
tests/test_models.py::TestSceneModels::test_face_item_valid PASSED
tests/test_models.py::TestSceneModels::test_scene_hit_valid PASSED
...
tests/test_ingest.py::TestSceneIngest::test_scene_ingest_valid_format PASSED
tests/test_search_formats.py::TestSceneSearchFormat::test_scene_search_response_structure PASSED

======================== 50 passed in 2.34s ========================
```
