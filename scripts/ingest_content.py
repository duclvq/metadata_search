"""
Script đọc data từ file JSON (format MongoDB-like) và push lên API ingest content.

Usage:
    python scripts/ingest_content.py                          # mặc định đọc scripts/sample_data.json
    python scripts/ingest_content.py --file path/to/data.json
    python scripts/ingest_content.py --api http://localhost:8003
"""

import argparse
import json
import sys
from pathlib import Path

import requests

DEFAULT_API = "http://localhost:8003"
DEFAULT_FILE = Path(__file__).parent / "sample_data.json"


def transform_content(doc: dict) -> dict:
    """Chuyển 1 document (format nguồn) thành ContentIngestItem cho API."""
    enriched = doc.get("enriched_data", {})
    description = enriched.get("audio", {}).get("summary", "")
    if not description:
        description = enriched.get("audio", {}).get("transcription", "")

    scene_list = enriched.get("scene_list", [])
    category = ""
    author = ""
    if scene_list:
        category = scene_list[0].get("category", "")
        author = scene_list[0].get("author", "")

    return {
        "content_id": doc["unique_id"],
        "title": doc.get("title", ""),
        "description": description,
        "tags": doc.get("video_tags", []),
        "duration_sec": doc.get("video_duration_sec") or 0.0,
        "created_at": doc.get("video_created_at", ""),
        "category": category,
        "author": author,
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest content data lên Metadata Search API")
    parser.add_argument("--file", type=str, default=str(DEFAULT_FILE), help="Đường dẫn file JSON")
    parser.add_argument("--api", type=str, default=DEFAULT_API, help="Base URL của API")
    parser.add_argument("--batch-size", type=int, default=50, help="Số content mỗi batch")
    args = parser.parse_args()

    # Đọc file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Không tìm thấy file: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    if isinstance(documents, dict):
        documents = [documents]

    # Transform tất cả documents thành contents
    all_contents = []
    for doc in documents:
        all_contents.append(transform_content(doc))

    print(f"Tổng cộng: {len(all_contents)} content")

    # Gửi theo batch
    endpoint = f"{args.api}/v1/contents/ingest"
    total_indexed = 0
    total_errors = []

    for i in range(0, len(all_contents), args.batch_size):
        batch = all_contents[i : i + args.batch_size]
        payload = {"contents": batch}

        try:
            resp = requests.post(endpoint, json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            total_indexed += result["indexed"]
            if result.get("errors"):
                total_errors.extend(result["errors"])
            print(f"  Batch {i // args.batch_size + 1}: indexed {result['indexed']} contents")
        except requests.exceptions.RequestException as e:
            print(f"  Batch {i // args.batch_size + 1}: LỖI - {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"    Response: {e.response.text}")

    print(f"\nKết quả: {total_indexed}/{len(all_contents)} content đã indexed")
    if total_errors:
        print(f"Lỗi ({len(total_errors)}):")
        for err in total_errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
