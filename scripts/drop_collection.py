"""Drop Milvus collection(s) and optionally recreate with current schema.

Usage:
    python -m scripts.drop_collection                       # drop all and recreate
    python -m scripts.drop_collection --collection scenes   # drop scenes only
    python -m scripts.drop_collection --collection contents # drop contents only
    python -m scripts.drop_collection --drop-only           # drop without recreating
"""

import argparse
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.config import settings
from src.milvus_client import get_milvus_client
from src.milvus_manager import ensure_collection


def main():
    parser = argparse.ArgumentParser(description="Drop Milvus collection(s)")
    parser.add_argument("--drop-only", action="store_true",
                        help="Drop without recreating")
    parser.add_argument("--collection", choices=["scenes", "contents", "all"],
                        default="all", help="Which collection(s) to drop (default: all)")
    args = parser.parse_args()

    client = get_milvus_client()

    collections = []
    if args.collection in ("scenes", "all"):
        collections.append(settings.milvus_collection_name)
    if args.collection in ("contents", "all"):
        collections.append(settings.milvus_content_collection_name)

    for name in collections:
        if not client.has_collection(collection_name=name):
            print(f"Collection '{name}' does not exist.")
            continue
        client.drop_collection(collection_name=name)
        print(f"Dropped collection '{name}'.")

    if not args.drop_only:
        ensure_collection(client)
        print("Recreated collection(s) with current schema.")


if __name__ == "__main__":
    main()
