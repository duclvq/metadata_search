# API Output Formats

## 1. Health Check

**`GET /health`**

```json
{ "status": "ok" }
```

---

## 2. Ingest APIs

### 2.1 `POST /v1/scenes/ingest`

**Response model:** `IngestResponse`

```json
{
  "indexed": 5,
  "errors": []
}
```

| Field     | Type       | Mô tả                                  |
| --------- | ---------- | --------------------------------------- |
| `indexed` | `int`      | Số lượng scene được index thành công    |
| `errors`  | `string[]` | Danh sách lỗi (nếu có, OpenSearch only) |

### 2.2 `POST /v1/contents/ingest`

**Response model:** `IngestResponse` — cấu trúc giống 2.1.

---

## 3. Scene Search APIs

### 3.1 `GET /v1/search/scene`

**Params:** `query_text`, `k`, `search_type` (semantic | fulltext | hybrid)

**Response model:** `SearchResponse`

```json
{
  "total": 42,
  "hits": [ /* SceneHit[] */ ],
  "facets": { /* Facets | null */ }
}
```

### 3.2 `POST /v1/search/scene/filter`

**Response model:** `SearchResponse` — cấu trúc giống 3.1.

### SceneHit

| Field                  | Type         | Mô tả                          |
| ---------------------- | ------------ | ------------------------------- |
| `score`                | `float`      | Điểm relevance                  |
| `scene_id`             | `string`     | ID scene                        |
| `scene_description`    | `string`     | Mô tả scene                     |
| `visual_caption`       | `string`     | Caption từ visual analysis       |
| `audio_summarization`  | `string`     | Tóm tắt audio                   |
| `audio_transcription`  | `string`     | Transcript audio                 |
| `faces`                | `FaceItem[]` | Danh sách khuôn mặt             |
| `start_time_sec`       | `float`      | Thời gian bắt đầu (giây)        |
| `end_time_sec`         | `float`      | Thời gian kết thúc (giây)       |
| `content_id`           | `string`     | ID video chứa scene              |
| `video_title`          | `string`     | Tiêu đề video                   |
| `video_name`           | `string`     | Tên file video                   |
| `video_summary`        | `string`     | Tóm tắt video                   |
| `video_tags`           | `string[]`   | Tags video                       |
| `video_duration_sec`   | `float`      | Thời lượng video (giây)          |
| `video_created_at`     | `string`     | Ngày tạo video                   |
| `resolution`           | `string`     | Độ phân giải                     |
| `fps`                  | `float`      | Frame per second                  |
| `program_id`           | `string`     | ID chương trình                  |
| `broadcast_date`       | `string`     | Ngày phát sóng                   |
| `content_type_id`      | `string`     | Loại nội dung                    |
| `category`             | `string`     | Danh mục                         |
| `created_date`         | `string`     | Ngày tạo record                  |
| `author`               | `string`     | Tác giả                          |

### FaceItem

```json
{ "face_id": "f001", "name": "Nguyen Van A" }
```

### Facets

| Field             | Type           | Mô tả                       |
| ----------------- | -------------- | ---------------------------- |
| `category`        | `FacetItem[]`  | Facet theo danh mục          |
| `created_date`    | `FacetItem[]`  | Facet theo ngày tạo          |
| `author`          | `FacetItem[]`  | Facet theo tác giả           |
| `broadcast_date`  | `FacetItem[]`  | Facet theo ngày phát sóng    |
| `program_id`      | `FacetItem[]`  | Facet theo chương trình      |
| `content_type_id` | `FacetItem[]`  | Facet theo loại nội dung     |

**FacetItem:** `{ "value": "...", "count": 3, "scene_ids": ["s1","s2","s3"] }`

---

## 4. Content Search APIs

### 4.1 `GET /v1/search/content`

**Params:** `query_text`, `k`, `search_type` (semantic | fulltext | hybrid)

**Response model:** `ContentSearchResponse`

```json
{
  "total": 10,
  "hits": [ /* ContentHit[] */ ],
  "facets": { /* ContentFacets | null */ }
}
```

### 4.2 `POST /v1/search/content/filter`

**Response model:** `ContentSearchResponse` — cấu trúc giống 4.1.

### ContentHit

| Field             | Type       | Mô tả                  |
| ----------------- | ---------- | ----------------------- |
| `score`           | `float`    | Điểm relevance          |
| `content_id`      | `string`   | ID nội dung             |
| `title`           | `string`   | Tiêu đề                 |
| `description`     | `string`   | Mô tả                   |
| `video_summary`   | `string`   | Tóm tắt video           |
| `tags`            | `string[]` | Tags                     |
| `duration_sec`    | `float`    | Thời lượng (giây)       |
| `created_at`      | `string`   | Ngày tạo                |
| `category`        | `string`   | Danh mục                |
| `author`          | `string`   | Tác giả                 |
| `video_name`      | `string`   | Tên file video          |
| `resolution`      | `string`   | Độ phân giải            |
| `fps`             | `float`    | Frame per second         |
| `program_id`      | `string`   | ID chương trình         |
| `broadcast_date`  | `string`   | Ngày phát sóng          |
| `content_type_id` | `string`   | Loại nội dung           |

### ContentFacets

| Field             | Type                  | Mô tả                   |
| ----------------- | --------------------- | ------------------------ |
| `category`        | `ContentFacetItem[]`  | Facet theo danh mục      |
| `author`          | `ContentFacetItem[]`  | Facet theo tác giả       |
| `broadcast_date`  | `ContentFacetItem[]`  | Facet theo ngày phát sóng|
| `program_id`      | `ContentFacetItem[]`  | Facet theo chương trình  |
| `content_type_id` | `ContentFacetItem[]`  | Facet theo loại nội dung |

**ContentFacetItem:** `{ "value": "...", "count": 2, "content_ids": ["c1","c2"] }`

---

## 5. List APIs

### 5.1 `GET /v1/search/scene/list`

**Params:** `skip`, `limit`

```json
{
  "total": 20,
  "items": [ /* scene objects (same fields as SceneHit, without score) */ ]
}
```

### 5.2 `GET /v1/search/content/list`

**Params:** `skip`, `limit`

```json
{
  "total": 5,
  "items": [ /* content objects (same fields as ContentHit, without score) */ ]
}
```

---

## 6. Face Search APIs

### 6.1 `POST /v1/face_search`

**Input:** `images` (file upload) và/hoặc `face_names` (form), `k`

**Response model:** `SearchResponse` — cấu trúc giống mục 3 (Scene Search).

### 6.2 `POST /v1/face_search/filter`

**Response model:** `SearchResponse` — cấu trúc giống mục 3.

---

## 7. CRUD APIs (`/v1/videos` — hiện đang disabled)

### 7.1 `POST /v1/videos` — Tạo video

**Response model:** `SyncResult`

```json
{ "mongo_id": "665a...", "scenes_synced": 12 }
```

### 7.2 `GET /v1/videos` — Danh sách video

**Response model:** `VideoListResponse`

```json
{ "total": 100, "items": [ { "_id": "...", "unique_id": "...", "status": "...", ... } ] }
```

### 7.3 `GET /v1/videos/{unique_id}` — Chi tiết video

Trả về full MongoDB document (dict).

### 7.4 `PUT /v1/videos/{unique_id}` — Cập nhật video

**Response model:** `SyncResult` — giống 7.1.

### 7.5 `DELETE /v1/videos/{unique_id}` — Xoá video

**Response model:** `DeleteResult`

```json
{ "deleted": true, "scenes_removed": 12 }
```

### 7.6 `POST /v1/videos/{unique_id}/sync` — Sync thủ công

**Response model:** `SyncResult` — giống 7.1.

### 7.7 `POST /v1/videos/sync-all` — Sync toàn bộ

```json
{ "videos_synced": 50, "scenes_synced": 600, "contents_synced": 50 }
```
