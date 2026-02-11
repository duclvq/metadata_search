# Metadata Search

Video scene search service: MongoDB → Vector DB (Milvus/OpenSearch) with auto-sync.

## Yêu cầu

- Python 3.11+
- MongoDB 6+ (replica set)
- Milvus hoặc OpenSearch

## Cài đặt

```bash
pip install -r requirements.txt
```

## Cấu hình

Chỉnh sửa file `.env`:

```env
MS_BACKEND=milvus

# MongoDB
MS_MONGO_URI=mongodb://localhost:27017/?replicaSet=rs0
MS_MONGO_DB=Metadata_Enrichment
MS_MONGO_COLLECTION=video_queue

# Milvus
MS_MILVUS_URI=http://localhost:19530
MS_MILVUS_COLLECTION_NAME=scenes
MS_EMBEDDING_DIMENSION=1024
MS_EMBEDDING_MODEL_NAME=BAAI/bge-m3
MS_EMBEDDING_DEVICE=cuda
```

## Khởi động MongoDB Replica Set

MongoDB **bắt buộc** chạy replica set để sử dụng change stream.

```bash
# Khởi tạo replica set (chạy 1 lần duy nhất)
mongosh --eval "rs.initiate()"
```

Hoặc thêm vào `mongod.cfg`:

```yaml
replication:
  replSetName: rs0
```

## Khởi động Milvus

```bash
docker compose -f dockers/milvus/docker-compose.yml up -d
```

## Chạy API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

## Chạy Watcher (MongoDB → Vector DB)

```bash
# Chạy bình thường — theo dõi thay đổi realtime
python -m scripts.mongo_watcher

# Sync toàn bộ data cũ rồi mới watch
python -m scripts.mongo_watcher --full-sync

# Chỉ sync 1 lần, không watch
python -m scripts.mongo_watcher --full-sync-only

# Reset vị trí theo dõi (bắt đầu từ hiện tại)
python -m scripts.mongo_watcher --reset-token
```

## Quản lý Milvus Collection

```bash
# Xoá collection và tạo lại với schema mới
python -m scripts.drop_collection

# Chỉ xoá, không tạo lại
python -m scripts.drop_collection --drop-only
```

> **Lưu ý**: API không tự động xoá collection khi khởi động. Nếu schema thay đổi,
> bạn cần chạy lệnh trên để xoá và tạo lại, sau đó sync lại data bằng
> `python -m scripts.mongo_watcher --full-sync-only`.

### Cài watcher như Windows Service (nssm)

```bash
nssm install MongoWatcher "C:\path\to\python.exe" "-m scripts.mongo_watcher"
nssm set MongoWatcher AppDirectory "D:\py_source\metadata_search"
nssm start MongoWatcher
```

## API Endpoints

### Search

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `GET` | `/v1/search/semantic?query_text=...&k=5` | Tìm kiếm ngữ nghĩa |
| `GET` | `/v1/search/hybrid?query_text=...&k=10` | Tìm kiếm kết hợp (BM25 + vector) |
| `POST` | `/v1/search/filter` | Tìm kiếm với filter |

### CRUD (MongoDB + auto-sync Vector DB)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `GET` | `/v1/videos` | Danh sách video (`?status=completed`) |
| `GET` | `/v1/videos/{unique_id}` | Chi tiết 1 video |
| `POST` | `/v1/videos` | Thêm video mới |
| `PUT` | `/v1/videos/{unique_id}` | Cập nhật video |
| `DELETE` | `/v1/videos/{unique_id}` | Xóa video |
| `POST` | `/v1/videos/{unique_id}/sync` | Sync lại 1 video vào vector DB |
| `POST` | `/v1/videos/sync-all` | Sync toàn bộ video |

### Ingest (trực tiếp vào Vector DB)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| `POST` | `/v1/scenes/ingest` | Ingest scenes trực tiếp |

## Kiến trúc

```
MongoDB (video_queue)
    │
    ├── Change Stream ──► mongo_watcher.py ──► Vector DB
    │                                          (Milvus / OpenSearch)
    └── CRUD API (/v1/videos) ──auto-sync──►
```

- **Watcher**: chạy nền, theo dõi mọi thay đổi trong MongoDB, tự động sync sang vector DB
- **CRUD API**: thao tác CRUD trên MongoDB, mỗi thao tác ghi tự động sync vector DB
- **Resume token**: lưu vào `resume_token.json`, watcher restart không mất event
