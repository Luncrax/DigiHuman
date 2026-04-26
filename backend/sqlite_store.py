"""
SQLite-backed persistence for DigiHuman.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Optional


DB_PATH = Path("data/digihuman.db")


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


@dataclass
class AuthUser:
    id: int
    username: str
    created_at: str


class SQLiteStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure_schema()
        self._migrate_json_histories()
        self._migrate_character_config_file()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS histories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_uid TEXT NOT NULL,
                    history_uid TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(owner_uid, history_uid)
                );

                CREATE TABLE IF NOT EXISTS history_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_uid TEXT NOT NULL,
                    history_uid TEXT NOT NULL,
                    role TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    name TEXT,
                    avatar TEXT
                );

                CREATE TABLE IF NOT EXISTS character_configs (
                    owner_uid TEXT PRIMARY KEY,
                    llm_system_prompt TEXT NOT NULL DEFAULT '',
                    emotion_style TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                """
            )

    def _migrate_json_histories(self) -> None:
        history_root = Path("chat_history")
        if not history_root.exists():
            return

        with self._lock, self._connect() as conn:
            for owner_dir in history_root.iterdir():
                if not owner_dir.is_dir():
                    continue

                owner_uid = owner_dir.name
                for file_path in owner_dir.glob("*.json"):
                    history_uid = file_path.stem
                    existing = conn.execute(
                        "SELECT 1 FROM histories WHERE owner_uid = ? AND history_uid = ?",
                        (owner_uid, history_uid),
                    ).fetchone()
                    if existing:
                        continue

                    try:
                        payload = json.loads(file_path.read_text(encoding="utf-8"))
                    except Exception:
                        continue

                    metadata = {}
                    messages = []
                    for item in payload:
                        if item.get("role") == "metadata":
                            metadata = item
                        else:
                            messages.append(item)

                    created_at = metadata.get("timestamp") or datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(timespec="seconds")
                    updated_at = messages[-1]["timestamp"] if messages else created_at

                    conn.execute(
                        """
                        INSERT INTO histories (owner_uid, history_uid, created_at, updated_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (owner_uid, history_uid, created_at, updated_at, json.dumps(metadata, ensure_ascii=False)),
                    )

                    for message in messages:
                        conn.execute(
                            """
                            INSERT INTO history_messages (owner_uid, history_uid, role, timestamp, content, name, avatar)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                owner_uid,
                                history_uid,
                                message.get("role", ""),
                                message.get("timestamp") or created_at,
                                message.get("content", ""),
                                message.get("name"),
                                message.get("avatar"),
                            ),
                        )

    def _migrate_character_config_file(self) -> None:
        config_path = Path("data/character_config.json")
        if not config_path.exists():
            return

        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return

        owner_uid = "guest"
        existing = self.get_character_config(owner_uid)
        if existing.get("llm_system_prompt") or existing.get("emotion_style"):
            return

        self.save_character_config(
            owner_uid,
            str(payload.get("llm_system_prompt", "") or ""),
            str(payload.get("emotion_style", "") or ""),
        )

    def create_history(self, owner_uid: str, history_uid: str, created_at: Optional[str] = None) -> str:
        now = created_at or _utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO histories (owner_uid, history_uid, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (owner_uid, history_uid, now, now, json.dumps({"role": "metadata", "timestamp": now}, ensure_ascii=False)),
            )
        return history_uid

    def history_exists(self, owner_uid: str, history_uid: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM histories WHERE owner_uid = ? AND history_uid = ?",
                (owner_uid, history_uid),
            ).fetchone()
        return bool(row)

    def append_history_message(
        self,
        owner_uid: str,
        history_uid: str,
        role: str,
        content: str,
        name: str | None = None,
        avatar: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        now = timestamp or _utc_now_iso()
        self.create_history(owner_uid, history_uid, created_at=now)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO history_messages (owner_uid, history_uid, role, timestamp, content, name, avatar)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (owner_uid, history_uid, role, now, content, name, avatar),
            )
            conn.execute(
                "UPDATE histories SET updated_at = ? WHERE owner_uid = ? AND history_uid = ?",
                (now, owner_uid, history_uid),
            )

    def get_history_messages(self, owner_uid: str, history_uid: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, timestamp, content, name, avatar
                FROM history_messages
                WHERE owner_uid = ? AND history_uid = ?
                ORDER BY id ASC
                """,
                (owner_uid, history_uid),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_history_list(self, owner_uid: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            histories = conn.execute(
                """
                SELECT history_uid, created_at, updated_at
                FROM histories
                WHERE owner_uid = ?
                ORDER BY updated_at DESC
                """,
                (owner_uid,),
            ).fetchall()

            result: list[dict[str, Any]] = []
            for row in histories:
                latest = conn.execute(
                    """
                    SELECT role, content, timestamp
                    FROM history_messages
                    WHERE owner_uid = ? AND history_uid = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (owner_uid, row["history_uid"]),
                ).fetchone()

                if latest:
                    latest_message = dict(latest)
                    is_new = False
                    timestamp = latest["timestamp"]
                else:
                    latest_message = {
                        "role": "system",
                        "content": "新对话",
                        "timestamp": row["created_at"],
                    }
                    is_new = True
                    timestamp = row["created_at"]

                result.append(
                    {
                        "uid": row["history_uid"],
                        "latest_message": latest_message,
                        "timestamp": timestamp,
                        "is_new": is_new,
                    }
                )
        return result

    def delete_history(self, owner_uid: str, history_uid: str) -> bool:
        with self._lock, self._connect() as conn:
            conn.execute(
                "DELETE FROM history_messages WHERE owner_uid = ? AND history_uid = ?",
                (owner_uid, history_uid),
            )
            deleted = conn.execute(
                "DELETE FROM histories WHERE owner_uid = ? AND history_uid = ?",
                (owner_uid, history_uid),
            ).rowcount
        return bool(deleted)

    def modify_latest_message(self, owner_uid: str, history_uid: str, role: str, new_content: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, role
                FROM history_messages
                WHERE owner_uid = ? AND history_uid = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (owner_uid, history_uid),
            ).fetchone()
            if not row or row["role"] != role:
                return False
            conn.execute(
                "UPDATE history_messages SET content = ? WHERE id = ?",
                (new_content, row["id"]),
            )
        return True

    def save_character_config(self, owner_uid: str, llm_system_prompt: str, emotion_style: str) -> dict[str, str]:
        now = _utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO character_configs (owner_uid, llm_system_prompt, emotion_style, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(owner_uid) DO UPDATE SET
                    llm_system_prompt = excluded.llm_system_prompt,
                    emotion_style = excluded.emotion_style,
                    updated_at = excluded.updated_at
                """,
                (owner_uid, llm_system_prompt, emotion_style, now),
            )
        return {
            "llm_system_prompt": llm_system_prompt,
            "emotion_style": emotion_style,
        }

    def get_character_config(self, owner_uid: str) -> dict[str, str]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT llm_system_prompt, emotion_style FROM character_configs WHERE owner_uid = ?",
                (owner_uid,),
            ).fetchone()
        if not row:
            return {"llm_system_prompt": "", "emotion_style": ""}
        return {
            "llm_system_prompt": row["llm_system_prompt"] or "",
            "emotion_style": row["emotion_style"] or "",
        }

    def register_user(self, username: str, password: str) -> AuthUser:
        normalized = username.strip()
        if len(normalized) < 3:
            raise ValueError("用户名至少需要 3 个字符。")
        if len(password) < 6:
            raise ValueError("密码至少需要 6 个字符。")

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        created_at = _utc_now_iso()

        with self._lock, self._connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (normalized, password_hash, salt, created_at),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("用户名已存在。") from exc

        return AuthUser(id=int(cursor.lastrowid), username=normalized, created_at=created_at)

    def login_user(self, username: str, password: str) -> tuple[AuthUser, str]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt, created_at FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()

        if not row:
            raise ValueError("用户名或密码错误。")

        expected = self._hash_password(password, row["salt"])
        if not hmac.compare_digest(expected, row["password_hash"]):
            raise ValueError("用户名或密码错误。")

        user = AuthUser(id=row["id"], username=row["username"], created_at=row["created_at"])
        token = self._create_auth_token(user.id)
        self.ensure_owner_records_for_user(user)
        return user, token

    def _create_auth_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now = _utc_now_iso()
        expires_at = (datetime.utcnow() + timedelta(days=30)).replace(microsecond=0).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_tokens (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, now, expires_at),
            )
        return token

    def get_user_by_token(self, token: str | None) -> Optional[AuthUser]:
        if not token:
            return None

        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.username, u.created_at, t.expires_at
                FROM auth_tokens t
                JOIN users u ON u.id = t.user_id
                WHERE t.token = ?
                """,
                (token,),
            ).fetchone()

        if not row:
            return None

        expires_at = row["expires_at"]
        if expires_at and expires_at < _utc_now_iso():
            self.logout_token(token)
            return None

        return AuthUser(id=row["id"], username=row["username"], created_at=row["created_at"])

    def logout_token(self, token: str | None) -> None:
        if not token:
            return
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))

    def ensure_owner_records_for_user(self, user: AuthUser) -> None:
        owner_uid = self.owner_uid_for_user(user)
        existing = self.get_character_config(owner_uid)
        if not existing["llm_system_prompt"] and not existing["emotion_style"]:
            guest = self.get_character_config("guest")
            if guest["llm_system_prompt"] or guest["emotion_style"]:
                self.save_character_config(owner_uid, guest["llm_system_prompt"], guest["emotion_style"])

    def get_debug_snapshot(self, limit: int = 20) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit), 100))
        with self._lock, self._connect() as conn:
            counts = {
                "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "auth_tokens": conn.execute("SELECT COUNT(*) FROM auth_tokens").fetchone()[0],
                "histories": conn.execute("SELECT COUNT(*) FROM histories").fetchone()[0],
                "history_messages": conn.execute("SELECT COUNT(*) FROM history_messages").fetchone()[0],
                "character_configs": conn.execute("SELECT COUNT(*) FROM character_configs").fetchone()[0],
            }

            users = [
                dict(row) for row in conn.execute(
                    "SELECT id, username, created_at FROM users ORDER BY id DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            ]
            histories = [
                dict(row) for row in conn.execute(
                    "SELECT owner_uid, history_uid, created_at, updated_at FROM histories ORDER BY updated_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            ]
            character_configs = [
                dict(row) for row in conn.execute(
                    "SELECT owner_uid, llm_system_prompt, emotion_style, updated_at FROM character_configs ORDER BY updated_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            ]

            history_messages = []
            for row in conn.execute(
                """
                SELECT id, owner_uid, history_uid, role, timestamp, content, name, avatar
                FROM history_messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall():
                payload = dict(row)
                content = str(payload.get("content", "") or "")
                payload["content_preview"] = content[:120]
                payload.pop("content", None)
                history_messages.append(payload)

            auth_tokens = []
            for row in conn.execute(
                "SELECT token, user_id, created_at, expires_at FROM auth_tokens ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall():
                payload = dict(row)
                token = str(payload.get("token", "") or "")
                payload["token_preview"] = f"{token[:10]}..." if token else ""
                payload.pop("token", None)
                auth_tokens.append(payload)

        return {
            "db_path": str(self.db_path.resolve()),
            "counts": counts,
            "tables": {
                "users": users,
                "auth_tokens": auth_tokens,
                "histories": histories,
                "history_messages": history_messages,
                "character_configs": character_configs,
            },
        }

    @staticmethod
    def owner_uid_for_user(user: AuthUser) -> str:
        return f"user:{user.id}"

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()


_store: SQLiteStore | None = None


def get_sqlite_store() -> SQLiteStore:
    global _store
    if _store is None:
        _store = SQLiteStore()
    return _store
