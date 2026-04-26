from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from .milvus_store import KnowledgeItem

KNOWLEDGE_ROOT = Path("study_assets/knowledge")
TEXT_EXTENSIONS = {".md", ".txt"}
JSON_EXTENSIONS = {".json"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | JSON_EXTENSIONS


def chunk_text(text: str, chunk_size: int = 320, overlap: int = 40) -> list[str]:
    normalized = " ".join((text or "").split())
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def stable_int_id(source: str) -> int:
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:15]
    return int(digest, 16)


def build_item_from_chunk(file_path: Path, chunk: str, index: int) -> KnowledgeItem:
    title = file_path.stem.replace("_", " ")
    item_type = "resource"
    category = file_path.parent.name if file_path.parent != KNOWLEDGE_ROOT else "study_material"
    payload = {
        "source": str(file_path.as_posix()),
        "chunk_index": index,
        "format": file_path.suffix.lower().lstrip("."),
    }
    uid = stable_int_id(f"{file_path.as_posix()}::{index}")
    return KnowledgeItem(
        id=uid,
        owner_uid="system",
        item_type=item_type,
        title=title,
        description=chunk,
        category=category,
        tool_command="",
        payload=payload,
    )


def iter_text_items(file_path: Path) -> Iterable[KnowledgeItem]:
    content = file_path.read_text(encoding="utf-8")
    for index, chunk in enumerate(chunk_text(content), start=1):
        yield build_item_from_chunk(file_path, chunk, index)


def iter_json_items(file_path: Path) -> Iterable[KnowledgeItem]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError(f"Unsupported JSON payload in {file_path}")

    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or file_path.stem).strip()
        description = str(item.get("description") or "").strip()
        if not description:
            continue
        uid = stable_int_id(f"{file_path.as_posix()}::{index}::{title}")
        yield KnowledgeItem(
            id=uid,
            owner_uid=str(item.get("owner_uid") or "system"),
            item_type=str(item.get("item_type") or "resource"),
            title=title,
            description=description,
            category=str(item.get("category") or "study_material"),
            tool_command=str(item.get("tool_command") or ""),
            payload={
                "source": str(file_path.as_posix()),
                "format": "json",
                **(item.get("payload") or {}),
            },
        )


def iter_knowledge_items_from_paths(paths: list[Path]) -> list[KnowledgeItem]:
    items: list[KnowledgeItem] = []
    for file_path in sorted(paths):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            items.extend(iter_text_items(file_path))
        elif suffix in JSON_EXTENSIONS:
            items.extend(iter_json_items(file_path))
    return items


def iter_knowledge_items(root: Path) -> list[KnowledgeItem]:
    files = [
        file_path
        for file_path in root.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return iter_knowledge_items_from_paths(files)


def resolve_relative_knowledge_path(relative_path: str, root: Path = KNOWLEDGE_ROOT) -> Path:
    target = (root / relative_path).resolve()
    root_resolved = root.resolve()
    if root_resolved not in target.parents and target != root_resolved:
        raise ValueError("Invalid knowledge path.")
    return target


def list_knowledge_files(root: Path = KNOWLEDGE_ROOT) -> list[dict]:
    entries: list[dict] = []
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        entries.append(
            {
                "name": file_path.name,
                "relative_path": file_path.relative_to(root).as_posix(),
                "size": file_path.stat().st_size,
                "suffix": file_path.suffix.lower(),
            }
        )
    return entries
