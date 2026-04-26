"""
Per-request owner context for user-specific configuration.
"""
from contextvars import ContextVar, Token


_owner_uid_var: ContextVar[str] = ContextVar("owner_uid", default="guest")


def get_current_owner_uid() -> str:
    return _owner_uid_var.get()


def set_current_owner_uid(owner_uid: str) -> Token:
    return _owner_uid_var.set(owner_uid or "guest")


def reset_current_owner_uid(token: Token) -> None:
    _owner_uid_var.reset(token)
