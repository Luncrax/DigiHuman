"""
Persistent character configuration for LLM prompt and expression style.
"""
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Dict


@dataclass
class CharacterConfig:
    llm_system_prompt: str = ""
    emotion_style: str = ""


class CharacterConfigStore:
    def __init__(self, file_path: Path | None = None):
        self.file_path = file_path or Path("data/character_config.json")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def load(self) -> CharacterConfig:
        with self._lock:
            if not self.file_path.exists():
                return CharacterConfig()

            try:
                payload = json.loads(self.file_path.read_text(encoding="utf-8"))
            except Exception:
                return CharacterConfig()

            return CharacterConfig(
                llm_system_prompt=str(payload.get("llm_system_prompt", "") or ""),
                emotion_style=str(payload.get("emotion_style", "") or ""),
            )

    def save(self, config: CharacterConfig) -> CharacterConfig:
        with self._lock:
            self.file_path.write_text(
                json.dumps(asdict(config), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return config

    def to_dict(self) -> Dict[str, str]:
        return asdict(self.load())


_store: CharacterConfigStore | None = None


def get_character_config_store() -> CharacterConfigStore:
    global _store
    if _store is None:
        _store = CharacterConfigStore()
    return _store


def get_character_config() -> CharacterConfig:
    return get_character_config_store().load()

