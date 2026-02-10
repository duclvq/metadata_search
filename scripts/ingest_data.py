"""
Script đọc data từ file JSON (format MongoDB-like) và push lên API ingest.

Usage:
    python scripts/ingest_data.py                          # mặc định đọc scripts/sample_data.json
    python scripts/ingest_data.py --file path/to/data.json
    python scripts/ingest_data.py --api http://localhost:8000
"""

import argparse
import json
import sys
from pathlib import Path

import requests

DEFAULT_API = "http://localhost:8003"
DEFAULT_FILE = Path(__file__).parent / "sample_data.json"


def parse_time_to_sec(time_str: str) -> float:
    """Chuyển 'HH:MM:SS.mmm' thành giây."""
    parts = time_str.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def transform(doc: dict) -> list[dict]:
    """Chuyển 1 document (format nguồn) thành danh sách SceneIngestItem cho API."""
    enriched = doc["enriched_data"]
    scenes = []

    for scene in enriched["scene_list"]:
        # Kết hợp scene_captioning + audio_summary thành scene_description
        caption = scene.get("scene_captioning", "")
        audio_summary = scene.get("audio_summary", "")
        description = f"{caption}\n{audio_summary}".strip() if audio_summary else caption

        scenes.append({
            "scene_id": scene["scene_id"],
            "scene_description": description,
            "start_time_sec": parse_time_to_sec(scene["start"]),
            "end_time_sec": parse_time_to_sec(scene["end"]),
            "video": {
                "video_id": doc["unique_id"],
                "video_title": doc.get("title", ""),
                "video_description": enriched.get("audio", {}).get("summary", ""),
                "video_tags": doc.get("video_tags", []),
                "video_duration_sec": doc.get("video_duration_sec"),
                "video_created_at": doc.get("video_created_at"),
            },
            "category": scene.get("category", ""),
            "created_date": scene.get("created_date", ""),
            "author": scene.get("author", ""),
        })

    return scenes


def main():
    parser = argparse.ArgumentParser(description="Ingest data lên Metadata Search API")
    parser.add_argument("--file", type=str, default=str(DEFAULT_FILE), help="Đường dẫn file JSON")
    parser.add_argument("--api", type=str, default=DEFAULT_API, help="Base URL của API")
    parser.add_argument("--batch-size", type=int, default=50, help="Số scene mỗi batch")
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

    # Transform tất cả documents thành scenes
    all_scenes = []
    for doc in documents:
        all_scenes.extend(transform(doc))

    print(f"Tổng cộng: {len(documents)} video, {len(all_scenes)} scene")

    # Gửi theo batch
    endpoint = f"{args.api}/v1/scenes/ingest"
    total_indexed = 0
    total_errors = []

    for i in range(0, len(all_scenes), args.batch_size):
        batch = all_scenes[i : i + args.batch_size]
        payload = {"scenes": batch}

        try:
            resp = requests.post(endpoint, json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            total_indexed += result["indexed"]
            if result.get("errors"):
                total_errors.extend(result["errors"])
            print(f"  Batch {i // args.batch_size + 1}: indexed {result['indexed']} scenes")
        except requests.exceptions.RequestException as e:
            print(f"  Batch {i // args.batch_size + 1}: LỖI - {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"    Response: {e.response.text}")

    print(f"\nKết quả: {total_indexed}/{len(all_scenes)} scene đã indexed")
    if total_errors:
        print(f"Lỗi ({len(total_errors)}):")
        for err in total_errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
