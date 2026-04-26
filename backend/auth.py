"""
Simple token-based authentication backed by SQLite.
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from backend.sqlite_store import AuthUser, get_sqlite_store


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def get_current_user_from_authorization(authorization: str | None) -> AuthUser | None:
    token = extract_bearer_token(authorization)
    return get_sqlite_store().get_user_by_token(token)


def require_current_user(authorization: str | None = Header(default=None)) -> AuthUser:
    user = get_current_user_from_authorization(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录。")
    return user
