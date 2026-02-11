# API Search - Output Formats

Tài liệu mô tả output của các API search trong hệ thống.

## Tóm tắt các API

Hệ thống cung cấp 7 API search chính:

| # | Endpoint | Method | Mô tả |
|---|----------|--------|-------|
| 1 | `/v1/search/scene` | GET | Tìm kiếm scene theo text query (semantic/fulltext/hybrid) |
| 2 | `/v1/search/scene/filter` | POST | Tìm kiếm scene với bộ lọc metadata (category, author, date...) |
| 3 | `/v1/search/content` | GET | Tìm kiếm video/content theo text query |
| 4 | `/v1/search/content/filter` | POST | Tìm kiếm content với bộ lọc id |
| 5 | `/v1/search/scene/list` | GET | Liệt kê tất cả scene theo điều kiện (pagination, không tìm kiếm) |
| 6 | `/v1/search/conten/list | GET | Liệt kê tất cả content theo điều kiện (pagination, không tìm kiếm) |
**Loại response:**
- Scene APIs (1, 2, 5, 6): Trả về `SearchResponse` với `SceneHit[]` + facets
- Content APIs (3, 4): Trả về `ContentSearchResponse` với `ContentHit[]` + facets
- List API (7): Trả về `{ total, items[] }` (không có score và facets)

**Backend support:**
- OpenSearch: Hỗ trợ scene search (#1, #2) - chỉ semantic và hybrid
- Milvus: Hỗ trợ tất cả API - semantic, fulltext và hybrid

---

## 1. Scene Search

### 1.1 `GET /v1/search/scene`

**Tìm kiếm scene theo text query**

**Query params:**
- `query_text` (string, required): Từ khoá tìm kiếm
- `k` (int, default=10, max=100): Số lượng kết quả
- `search_type` (string, default="hybrid"): Loại tìm kiếm (semantic | fulltext | hybrid)

**Response:**

```json
{
  "total": 42,
  "hits": [
    {
      "score": 0.856,
      "scene_id": "video123_scene_001",
      "scene_description": "Hai người đang thảo luận về dự án",
      "visual_caption": "Two people in office meeting",
      "audio_summarization": "Thảo luận kế hoạch marketing Q1",
      "audio_transcription": "Chúng ta cần tăng ngân sách quảng cáo...",
      "faces": [
        {
          "face_id": "f001",
          "name": "Nguyen Van A"
        }
      ],
      "start_time_sec": 125.5,
      "end_time_sec": 148.2,
      "content_id": "video123",
      "video_title": "Họp team marketing tháng 1",
      "video_name": "meeting_jan_2026.mp4",
      "video_summary": "Cuộc họp bàn về chiến lược marketing",
      "video_tags": ["meeting", "marketing", "2026"],
      "video_duration_sec": 3600.0,
      "video_created_at": "2026-01-15T10:30:00",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal_meeting",
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe"
    }
  ],
  "facets": {
    "category": [
      {
        "value": "business",
        "count": 25,
        "scene_ids": ["scene001", "scene002", "..."]
      },
      {
        "value": "entertainment",
        "count": 17,
        "scene_ids": ["scene010", "scene011", "..."]
      }
    ],
    "created_date": [
      {
        "value": "2026-01-15",
        "count": 10,
        "scene_ids": ["scene001", "..."]
      }
    ],
    "author": [
      {
        "value": "John Doe",
        "count": 8,
        "scene_ids": ["scene001", "..."]
      }
    ],
    "broadcast_date": [],
    "program_id": [],
    "content_type_id": []
  }
}
```

### 1.2 `POST /v1/search/scene/filter`

**Tìm kiếm scene với bộ lọc metadata**

**Request body:**

```json
{
  "query_text": "họp marketing",
  "category": ["business", "education"],
  "author": ["John Doe"],
  "created_date": null,
  "broadcast_date": null,
  "program_id": null,
  "content_type_id": null,
  "k": 20,
  "search_type": "hybrid"
}
```
**Output**
Tương tự trên

---

## 2. Content Search

### 2.1 `GET /v1/search/content`

**Tìm kiếm video/content theo text query**

**Query params:**
- `query_text` (string, required): Từ khoá tìm kiếm
- `k` (int, default=10, max=100): Số lượng kết quả
- `search_type` (string, default="hybrid"): Loại tìm kiếm (semantic | fulltext | hybrid)

**Response:**

```json
{
  "total": 15,
  "hits": [
    {
      "score": 0.923,
      "content_id": "video123",
      "title": "Họp team marketing tháng 1",
      "description": "Cuộc họp bàn chiến lược marketing cho quý 1 năm 2026",
      "video_summary": "Thảo luận về kế hoạch marketing, ngân sách và mục tiêu",
      "tags": ["meeting", "marketing", "2026", "strategy"],
      "duration_sec": 3600.0,
      "created_at": "2026-01-15T10:30:00",
      "category": "business",
      "author": "John Doe",
      "video_name": "meeting_jan_2026.mp4",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal_meeting"
    }
  ],
  "facets": {
    "category": [
      {
        "value": "business",
        "count": 8,
        "content_ids": ["video123", "video124", "..."]
      }
    ],
    "author": [
      {
        "value": "John Doe",
        "count": 5,
        "content_ids": ["video123", "..."]
      }
    ],
    "broadcast_date": [],
    "program_id": [],
    "content_type_id": []
  }
}
```

### 2.2 `POST /v1/search/content/filter`

**Tìm kiếm content với bộ lọc metadata**

**Request body:**

```json
{
  "query_text": "marketing strategy",
  "category": ["business"],
  "author": null,
  "broadcast_date": null,
  "program_id": null,
  "content_type_id": null,
  "k": 20,
  "search_type": "semantic"
}
```
**Output**
Tương tự trên

---

## 3. Scene List

### 3.1 `GET /v1/search/scene/list`

**Liệt kê tất cả scene đã được index (không tìm kiếm)**

**Query params:**
- `skip` (int, default=0): Bỏ qua n kết quả đầu
- `limit` (int, default=20, max=1000): Số lượng kết quả mỗi trang

**Response:**

```json
{
  "total": 150,
  "items": [
    {
      "scene_id": "video123_scene_001",
      "scene_description": "Hai người đang thảo luận về dự án",
      "visual_caption": "Two people in office meeting",
      "audio_summarization": "Thảo luận kế hoạch marketing Q1",
      "audio_transcription": "Chúng ta cần tăng ngân sách quảng cáo...",
      "faces": [
        {
          "face_id": "f001",
          "name": "Nguyen Van A"
        }
      ],
      "start_time_sec": 125.5,
      "end_time_sec": 148.2,
      "content_id": "video123",
      "video_title": "Họp team marketing tháng 1",
      "video_name": "meeting_jan_2026.mp4",
      "video_summary": "Cuộc họp bàn về chiến lược marketing",
      "video_tags": ["meeting", "marketing", "2026"],
      "video_duration_sec": 3600.0,
      "video_created_at": "2026-01-15T10:30:00",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal_meeting",
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe"
    },
    {
      "scene_id": "video123_scene_002",
      "scene_description": "Trình bày slide về kết quả kinh doanh",
      "visual_caption": "Presentation with charts on screen",
      "audio_summarization": "Báo cáo doanh thu Q4",
      "audio_transcription": "Doanh thu quý 4 tăng 25% so với cùng kỳ...",
      "faces": [
        {
          "face_id": "f002",
          "name": "Tran Thi B"
        }
      ],
      "start_time_sec": 580.0,
      "end_time_sec": 685.3,
      "content_id": "video123",
      "video_title": "Họp team marketing tháng 1",
      "video_name": "meeting_jan_2026.mp4",
      "video_summary": "Cuộc họp bàn về chiến lược marketing",
      "video_tags": ["meeting", "marketing", "2026"],
      "video_duration_sec": 3600.0,
      "video_created_at": "2026-01-15T10:30:00",
      "resolution": "1920x1080",
      "fps": 30.0,
      "program_id": "prog_001",
      "broadcast_date": "2026-01-20",
      "content_type_id": "internal_meeting",
      "category": "business",
      "created_date": "2026-01-15",
      "author": "John Doe"
    }
  ]
}
```

**Lưu ý:**
- `total`: Tổng số scene trong hệ thống
- `items`: Danh sách scene (giống SceneHit nhưng **không có** field `score`)
- API này chỉ hỗ trợ backend Milvus
- Dùng để phân trang (pagination) toàn bộ dữ liệu scene đã index
