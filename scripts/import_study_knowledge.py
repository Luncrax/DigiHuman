from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.study_assistant.importer import KNOWLEDGE_ROOT, iter_knowledge_items
from backend.study_assistant.milvus_store import MilvusKnowledgeStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Import study knowledge into Milvus.")
    parser.add_argument("--root", default=str(KNOWLEDGE_ROOT), help="Knowledge root directory")
    parser.add_argument("--no-replace", action="store_true", help="Do not replace existing rows with the same IDs")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Knowledge directory does not exist: {root}")

    items = iter_knowledge_items(root)
    if not items:
        raise SystemExit("No importable knowledge files were found.")

    store = MilvusKnowledgeStore()
    result = store.import_items(items, replace=not args.no_replace)

    print(json.dumps({
        "root": str(root.resolve()),
        "items": len(items),
        "result": result,
        "milvus": store.get_status(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
