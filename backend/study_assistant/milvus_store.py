from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from backend.core.config import config
from backend.utils.logger import get_logger
from .embeddings import EMBEDDING_DIM, SimpleEmbeddingService

logger = get_logger(__name__)

try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )
except Exception as exc:  # pragma: no cover - optional dependency
    Collection = None
    CollectionSchema = None
    DataType = None
    FieldSchema = None
    connections = None
    utility = None
    _PYMILVUS_IMPORT_ERROR = str(exc)
else:
    _PYMILVUS_IMPORT_ERROR = ""


@dataclass
class KnowledgeItem:
    id: int
    owner_uid: str
    item_type: str
    title: str
    description: str
    category: str
    tool_command: str
    payload: dict[str, Any]

    def search_text(self) -> str:
        return " ".join(
            filter(
                None,
                [
                    self.title,
                    self.description,
                    self.category,
                    self.tool_command,
                    json.dumps(self.payload, ensure_ascii=False),
                ],
            )
        )


class MilvusKnowledgeStore:
    def __init__(self):
        self.embedding_service = SimpleEmbeddingService()
        self.collection_name = config.MILVUS_STUDY_COLLECTION
        self.available = False
        self.reason = ""
        self._collection = None
        self._fallback_items: list[KnowledgeItem] = []
        self._connect()

    def _connect(self) -> None:
        if not connections:
            self.reason = _PYMILVUS_IMPORT_ERROR or "pymilvus is not installed"
            logger.warning("Milvus disabled: %s", self.reason)
            return

        try:
            connections.connect(
                alias="study_assistant",
                host=config.MILVUS_HOST,
                port=str(config.MILVUS_PORT),
            )
            self.available = True
            logger.info("Milvus connected at %s:%s", config.MILVUS_HOST, config.MILVUS_PORT)
        except Exception as exc:  # pragma: no cover - environment dependent
            self.reason = str(exc)
            self.available = False
            logger.warning("Milvus unavailable: %s", exc)

    def ensure_collection(self) -> None:
        if not self.available:
            return
        if self._collection is not None:
            return

        if not utility.has_collection(self.collection_name, using="study_assistant"):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
                FieldSchema(name="owner_uid", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="item_type", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2048),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="tool_command", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="payload_json", dtype=DataType.VARCHAR, max_length=4096),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
            ]
            schema = CollectionSchema(fields=fields, description="Study assistant knowledge base")
            collection = Collection(self.collection_name, schema=schema, using="study_assistant")
            index_params = {
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            collection.create_index("embedding", index_params=index_params)
            self._collection = collection
        else:
            self._collection = Collection(self.collection_name, using="study_assistant")

        self._collection.load()

    def bootstrap(self, items: list[KnowledgeItem]) -> dict[str, Any]:
        self._fallback_items = items
        if not self.available:
            return {
                "status": "fallback",
                "reason": self.reason or "Milvus unavailable",
                "count": len(self._fallback_items),
            }

        try:
            self.ensure_collection()
            existing = self._collection.num_entities
            if existing > 0:
                return {"status": "ok", "backend": "milvus", "count": existing}
            self._insert_items(items, replace=False)
            return {"status": "ok", "backend": "milvus", "count": len(items)}
        except Exception as exc:  # pragma: no cover - environment dependent
            self.reason = str(exc)
            logger.warning("Milvus bootstrap failed, fallback enabled: %s", exc)
            return {"status": "fallback", "reason": str(exc), "count": len(self._fallback_items)}

    def import_items(self, items: list[KnowledgeItem], replace: bool = True) -> dict[str, Any]:
        if not items:
            return {"status": "error", "message": "No knowledge items to import."}

        existing_ids = {item.id for item in items}
        self._fallback_items = [item for item in self._fallback_items if item.id not in existing_ids]
        self._fallback_items.extend(items)

        if not self.available:
            return {
                "status": "fallback",
                "backend": "fallback",
                "count": len(items),
                "message": self.reason or "Milvus unavailable, items were only loaded into local fallback memory.",
            }

        self.ensure_collection()
        self._insert_items(items, replace=replace)
        return {
            "status": "ok",
            "backend": "milvus",
            "count": len(items),
            "collection_name": self.collection_name,
        }

    def delete_items_by_ids(self, ids: list[int]) -> dict[str, Any]:
        if not ids:
            return {"status": "ok", "backend": "milvus" if self.available else "fallback", "count": 0}

        id_set = set(ids)
        self._fallback_items = [item for item in self._fallback_items if item.id not in id_set]

        if not self.available:
            return {
                "status": "fallback",
                "backend": "fallback",
                "count": len(ids),
                "message": self.reason or "Milvus unavailable, only local fallback items were updated.",
            }

        self.ensure_collection()
        id_chunks = math.ceil(len(ids) / 500)
        for index in range(id_chunks):
            chunk = ids[index * 500:(index + 1) * 500]
            expr = f"id in [{','.join(str(value) for value in chunk)}]"
            self._collection.delete(expr)
        self._collection.flush()
        self._collection.load()
        return {
            "status": "ok",
            "backend": "milvus",
            "count": len(ids),
            "collection_name": self.collection_name,
        }

    def delete_items_by_source(self, source_path: str) -> dict[str, Any]:
        ids = [
            item.id
            for item in self._fallback_items
            if str(item.payload.get("source", "")) == source_path
        ]
        return self.delete_items_by_ids(ids)

    def _insert_items(self, items: list[KnowledgeItem], replace: bool) -> None:
        if not items:
            return

        ids = [item.id for item in items]
        if replace and ids:
            id_chunks = math.ceil(len(ids) / 500)
            for index in range(id_chunks):
                chunk = ids[index * 500:(index + 1) * 500]
                expr = f"id in [{','.join(str(value) for value in chunk)}]"
                self._collection.delete(expr)

        rows = []
        for item in items:
            rows.append(
                [
                    item.id,
                    item.owner_uid,
                    item.item_type,
                    item.title,
                    item.description,
                    item.category,
                    item.tool_command,
                    json.dumps(item.payload, ensure_ascii=False),
                    self.embedding_service.embed(item.search_text()),
                ]
            )

        columns = list(map(list, zip(*rows)))
        self._collection.insert(columns)
        self._collection.flush()
        self._collection.load()

    def search(self, owner_uid: str, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.available:
            try:
                self.ensure_collection()
                vector = [self.embedding_service.embed(query_text)]
                expr = f'owner_uid in ["system", "{owner_uid}"]'
                results = self._collection.search(
                    data=vector,
                    anns_field="embedding",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k,
                    expr=expr,
                    output_fields=["owner_uid", "item_type", "title", "description", "category", "tool_command", "payload_json"],
                )
                hits: list[dict[str, Any]] = []
                for hit in results[0]:
                    entity = hit.entity
                    payload_json = entity.get("payload_json") or "{}"
                    hits.append(
                        {
                            "score": float(hit.score),
                            "owner_uid": entity.get("owner_uid"),
                            "item_type": entity.get("item_type"),
                            "title": entity.get("title"),
                            "description": entity.get("description"),
                            "category": entity.get("category"),
                            "tool_command": entity.get("tool_command"),
                            "payload": json.loads(payload_json),
                        }
                    )
                return hits
            except Exception as exc:  # pragma: no cover - environment dependent
                self.reason = str(exc)
                logger.warning("Milvus search failed, fallback enabled: %s", exc)

        query_vector = self.embedding_service.embed(query_text)
        scored: list[tuple[float, KnowledgeItem]] = []
        for item in self._fallback_items:
            if item.owner_uid not in {"system", owner_uid}:
                continue
            item_vector = self.embedding_service.embed(item.search_text())
            score = sum(left * right for left, right in zip(query_vector, item_vector))
            scored.append((score, item))

        scored.sort(key=lambda entry: entry[0], reverse=True)
        return [
            {
                "score": round(score, 4),
                "owner_uid": item.owner_uid,
                "item_type": item.item_type,
                "title": item.title,
                "description": item.description,
                "category": item.category,
                "tool_command": item.tool_command,
                "payload": item.payload,
            }
            for score, item in scored[:top_k]
        ]

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "available": self.available,
            "backend": "milvus" if self.available else "fallback",
            "host": config.MILVUS_HOST,
            "port": config.MILVUS_PORT,
            "collection_name": self.collection_name,
            "import_error": _PYMILVUS_IMPORT_ERROR or None,
            "reason": self.reason or None,
            "fallback_items": len(self._fallback_items),
        }
