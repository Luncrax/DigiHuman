"""
Persistent character configuration backed by SQLite.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict

from backend.request_context import get_current_owner_uid
from backend.sqlite_store import get_sqlite_store


@dataclass
class CharacterConfig:
    llm_system_prompt: str = ""
    emotion_style: str = ""


class CharacterConfigStore:
    def __init__(self, owner_uid: str = "guest"):
        self.owner_uid = owner_uid
        self.store = get_sqlite_store()

    def load(self) -> CharacterConfig:
        payload = self.store.get_character_config(self.owner_uid)
        return CharacterConfig(
            llm_system_prompt=str(payload.get("llm_system_prompt", "") or ""),
            emotion_style=str(payload.get("emotion_style", "") or ""),
        )

    def save(self, config: CharacterConfig) -> CharacterConfig:
        self.store.save_character_config(
            self.owner_uid,
            config.llm_system_prompt,
            config.emotion_style,
        )
        return config

    def to_dict(self) -> Dict[str, str]:
        return asdict(self.load())


def get_character_config_store(owner_uid: str = "guest") -> CharacterConfigStore:
    resolved_owner_uid = owner_uid if owner_uid != "guest" else get_current_owner_uid()
    return CharacterConfigStore(owner_uid=resolved_owner_uid)


def get_character_config(owner_uid: str = "guest") -> CharacterConfig:
    return get_character_config_store(owner_uid).load()
