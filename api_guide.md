# Metadata Search API — Hướng dẫn sử dụng

Base URL: `http://localhost:8000`

---

## 1. Ingest Data (Nhập dữ liệu)

### Endpoint

```
POST /v1/scenes/ingest
Content-Type: application/json
```

### Request Body

```json
{
  "scenes": [
    {
      "scene_id": "89823b8d-0c67-4ca7-aa47-a5847eb87173",
      "scene_description": "Người đàn ông phát biểu trong phòng hội nghị lớn, cờ đỏ sao vàng trang trí sân khấu.\nPhát biểu khai mạc Đại hội Đảng lần thứ 14, nhấn mạnh vai trò lãnh đạo của Đảng.",
      "start_time_sec": 0.0,
      "end_time_sec": 161.56,
      "video": {
        "video_id": "79b7503e-f36b-1410-819a-009c3de8f61f",
        "video_title": "Đại hội Đảng lần thứ 14 - Phiên khai mạc",
        "video_description": "Đại hội 14 của Đảng diễn ra trong thời điểm lịch sử quan trọng.",
        "video_tags": ["đại hội đảng", "chính trị", "thời sự"],
        "video_duration_sec": 495.2,
        "video_created_at": "2025-01-15T08:00:00"
      }
    },
    {
      "scene_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "scene_description": "Toàn cảnh hội trường với hàng nghìn đại biểu ngồi chỉnh tề.\nBáo cáo về thành tựu phát triển kinh tế xã hội giai đoạn 2021-2025.",
      "start_time_sec": 161.56,
      "end_time_sec": 330.0,
      "video": {
        "video_id": "79b7503e-f36b-1410-819a-009c3de8f61f",
        "video_title": "Đại hội Đảng lần thứ 14 - Phiên khai mạc",
        "video_description": "Đại hội 14 của Đảng diễn ra trong thời điểm lịch sử quan trọng.",
        "video_tags": ["đại hội đảng", "chính trị", "thời sự"],
        "video_duration_sec": 495.2,
        "video_created_at": "2025-01-15T08:00:00"
      }
    }
  ]
}
```

### Response (thành công)

```json
{
  "indexed": 2,
  "errors": []
}
```

### Các field

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `scene_id` | **Có** | ID duy nhất của scene (dùng làm primary key, upsert nếu trùng) |
| `scene_description` | **Có** | Mô tả scene (nên kết hợp scene_captioning + audio_summary) |
| `start_time_sec` | **Có** | Thời điểm bắt đầu scene (giây) |
| `end_time_sec` | **Có** | Thời điểm kết thúc scene (giây) |
| `video.video_id` | **Có** | ID video chứa scene |
| `video.video_title` | **Có** | Tiêu đề video (dùng để tạo embedding) |
| `video.video_description` | Không | Mô tả / tóm tắt video |
| `video.video_tags` | Không | Danh sách tag, mặc định `[]` |
| `video.video_duration_sec` | Không | Tổng thời lượng video (giây) |
| `video.video_created_at` | Không | Ngày tạo video, format ISO 8601 |
| `category` | Không | Danh mục scene (vd: "chính trị", "giáo dục") |
| `created_date` | Không | Ngày tạo scene (vd: "2025-01-15") |
| `author` | Không | Tác giả / nguồn (vd: "VTV1", "Báo Tuổi Trẻ") |

---

## 2. Search (Tìm kiếm)

### 2.1 Semantic Search (tìm kiếm ngữ nghĩa)

```
GET /v1/search/semantic?query_text=đại hội đảng&k=5
```

### 2.2 Hybrid Search (kết hợp BM25 + vector)

```
GET /v1/search/hybrid?query_text=đại hội đảng&k=5
```

> Khi backend=milvus, hybrid sẽ tự động fallback về semantic search.

### Query Parameters

| Param | Bắt buộc | Mô tả |
|-------|----------|-------|
| `query_text` | **Có** | Nội dung tìm kiếm (tối thiểu 1 ký tự) |
| `k` | Không | Số kết quả trả về, mặc định `10`, tối đa `100` |

### Response

```json
{
  "total": 2,
  "hits": [
    {
      "score": 0.8234,
      "scene_id": "89823b8d-0c67-4ca7-aa47-a5847eb87173",
      "scene_description": "Người đàn ông phát biểu trong phòng hội nghị lớn...",
      "start_time_sec": 0.0,
      "end_time_sec": 161.56,
      "video_id": "79b7503e-f36b-1410-819a-009c3de8f61f",
      "video_title": "Đại hội Đảng lần thứ 14 - Phiên khai mạc",
      "video_description": "Đại hội 14 của Đảng diễn ra trong thời điểm lịch sử quan trọng.",
      "video_tags": ["đại hội đảng", "chính trị", "thời sự"],
      "category": "chính trị",
      "created_date": "2025-01-15",
      "author": "VTV1"
    }
  ],
  "facets": {
    "category": [
      {"value": "chính trị", "count": 2, "scene_ids": ["89823b8d-...", "a1b2c3d4-..."]},
      {"value": "thời sự", "count": 1, "scene_ids": ["11aa22bb-..."]}
    ],
    "created_date": [
      {"value": "2025-01-15", "count": 2, "scene_ids": ["89823b8d-...", "a1b2c3d4-..."]}
    ],
    "author": [
      {"value": "VTV1", "count": 2, "scene_ids": ["89823b8d-...", "a1b2c3d4-..."]}
    ]
  }
}
```

> `facets` chứa kết quả nhóm theo `category`, `created_date`, `author`. Mỗi nhóm gồm `value`, `count`, và danh sách `scene_ids` — dùng cho Filter API bên dưới.

---

## 3. Filter API (Lọc theo facets)

### Endpoint

```
POST /v1/search/filter
Content-Type: application/json
```

### Flow sử dụng

1. Search → nhận `facets` trong response
2. User chọn facet (vd: category = "chính trị") → lấy `scene_ids` từ facet đó
3. Gửi Filter request với `query_text` + `scene_ids` → chỉ tìm trong các scene đã lọc

### Request Body

```json
{
  "query_text": "đại hội đảng",
  "scene_ids": [
    "89823b8d-0c67-4ca7-aa47-a5847eb87173",
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6a7-8901-bcde-f12345678901"
  ],
  "k": 10
}
```

### Response

Cùng format với Search response (có `hits` + `facets`).

### Postman

1. Method: **POST**
2. URL: `http://localhost:8000/v1/search/filter`
3. Body → raw → JSON → dán request body ở trên
4. Nhấn **Send**

### cURL

```bash
curl -X POST http://localhost:8000/v1/search/filter \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "đại hội đảng",
    "scene_ids": ["89823b8d-0c67-4ca7-aa47-a5847eb87173", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    "k": 5
  }'
```

---

## 4. Hướng dẫn Postman (Ingest + Search)

### 3.1 Ingest Data

1. Tạo request mới, chọn method **POST**
2. URL: `http://localhost:8000/v1/scenes/ingest`
3. Tab **Headers**: thêm `Content-Type: application/json`
4. Tab **Body** → chọn **raw** → chọn **JSON**
5. Dán JSON body:

```json
{
  "scenes": [
    {
      "scene_id": "test-scene-001",
      "scene_description": "Học sinh ngồi trong lớp học hiện đại với máy tính bảng.\nGiới thiệu chương trình thí điểm lớp học thông minh tại 100 trường.",
      "start_time_sec": 0.0,
      "end_time_sec": 105.3,
      "video": {
        "video_id": "video-001",
        "video_title": "Chuyển đổi số trong giáo dục Việt Nam",
        "video_description": "Phóng sự về quá trình chuyển đổi số trong hệ thống giáo dục.",
        "video_tags": ["giáo dục", "chuyển đổi số"],
        "video_duration_sec": 550.0,
        "video_created_at": "2025-03-20T14:30:00"
      },
      "category": "giáo dục",
      "created_date": "2025-03-20",
      "author": "VTV2"
    }
  ]
}
```

6. Nhấn **Send**
7. Kết quả mong đợi (Status 200):

```json
{
  "indexed": 1,
  "errors": []
}
```

### 3.2 Semantic Search

1. Tạo request mới, chọn method **GET**
2. URL: `http://localhost:8000/v1/search/semantic`
3. Tab **Params**, thêm:
   - `query_text` = `lớp học thông minh`
   - `k` = `5`
4. URL sẽ thành: `http://localhost:8000/v1/search/semantic?query_text=lớp học thông minh&k=5`
5. Nhấn **Send**

### 3.3 Hybrid Search

Tương tự semantic, chỉ đổi endpoint:

```
GET http://localhost:8000/v1/search/hybrid?query_text=lớp học thông minh&k=5
```

### 3.4 Health Check

```
GET http://localhost:8000/health
```

Response: `{"status": "ok"}`

---

## 5. Ingest bằng Script

```bash
# Ingest sample data (10 scene, 3 video)
python scripts/ingest_data.py

# Ingest từ file khác
python scripts/ingest_data.py --file path/to/data.json

# Chỉ định API URL
python scripts/ingest_data.py --api http://localhost:8000

# Tuỳ chỉnh batch size
python scripts/ingest_data.py --batch-size 20
```

---

## 6. Ingest bằng cURL

```bash
curl -X POST http://localhost:8000/v1/scenes/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "scene_id": "curl-test-001",
        "scene_description": "Bão số 5 đổ bộ miền Trung, mưa lớn gió giật cấp 14.",
        "start_time_sec": 0.0,
        "end_time_sec": 90.0,
        "video": {
          "video_id": "video-bao-5",
          "video_title": "Thời sự: Bão số 5 đổ bộ miền Trung"
        }
      }
    ]
  }'
```

```bash
curl "http://localhost:8000/v1/search/semantic?query_text=bão+miền+trung&k=3"
```
