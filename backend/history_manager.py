"""
SQLite-backed chat history manager.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, List, TypedDict, Optional

from loguru import logger

from backend.sqlite_store import get_sqlite_store


class HistoryMessage(TypedDict):
    role: Literal["human", "ai"]
    timestamp: str
    content: str
    name: Optional[str]
    avatar: Optional[str]


def create_new_history(conf_uid: str) -> str:
    if not conf_uid:
        logger.warning("No conf_uid provided")
        return ""

    history_uid = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex}"
    get_sqlite_store().create_history(conf_uid, history_uid)
    return history_uid


def store_message(
    conf_uid: str,
    history_uid: str,
    role: Literal["human", "ai"],
    content: str,
    name: str | None = None,
    avatar: str | None = None,
):
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return

    get_sqlite_store().append_history_message(
        conf_uid,
        history_uid,
        role,
        content,
        name=name,
        avatar=avatar,
    )


def get_metadata(conf_uid: str, history_uid: str) -> dict:
    if not conf_uid or not history_uid:
        return {}

    histories = get_sqlite_store().get_history_list(conf_uid)
    for history in histories:
        if history["uid"] == history_uid:
            return {
                "role": "metadata",
                "timestamp": history.get("timestamp", ""),
            }
    return {}


def update_metadate(conf_uid: str, history_uid: str, metadata: dict) -> bool:
    if not conf_uid or not history_uid:
        return False

    store = get_sqlite_store()
    if not store.history_exists(conf_uid, history_uid):
        return False

    # Current app only needs metadata existence; keep this as a no-op success for compatibility.
    return True


def get_history(conf_uid: str, history_uid: str) -> List[HistoryMessage]:
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return []
    return get_sqlite_store().get_history_messages(conf_uid, history_uid)


def delete_history(conf_uid: str, history_uid: str) -> bool:
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return False
    return get_sqlite_store().delete_history(conf_uid, history_uid)


def get_history_list(conf_uid: str) -> List[dict]:
    if not conf_uid:
        return []
    return get_sqlite_store().get_history_list(conf_uid)


def modify_latest_message(
    conf_uid: str,
    history_uid: str,
    role: Literal["human", "ai", "system"],
    new_content: str,
) -> bool:
    if not conf_uid or not history_uid:
        logger.warning("Missing conf_uid or history_uid")
        return False
    return get_sqlite_store().modify_latest_message(conf_uid, history_uid, role, new_content)


def rename_history_file(conf_uid: str, old_history_uid: str, new_history_uid: str) -> bool:
    # SQLite-backed histories keep their original IDs stable; rename is not supported in the current app.
    return False


class HistoryManager:
    def __init__(self):
        self.store = get_sqlite_store()

    def create_new_history(self, client_uid: str) -> str:
        return create_new_history(client_uid)

    def get_history(self, client_uid: str, history_uid: str) -> List[HistoryMessage]:
        return get_history(client_uid, history_uid)

    def get_history_list(self, client_uid: str) -> List[dict]:
        return get_history_list(client_uid)

    def delete_history(self, client_uid: str, history_uid: str) -> bool:
        return delete_history(client_uid, history_uid)

    def store_message(self, client_uid: str, history_uid: str, role: str, content: str, name: str = None, avatar: str = None):
        store_message(client_uid, history_uid, role, content, name, avatar)
