"""CSRF protection utilities."""
from __future__ import annotations

import secrets
from typing import Any

from itsdangerous import URLSafeTimedSerializer

from twitch_ollama.config import settings


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def csrf_serializer() -> URLSafeTimedSerializer:
    """Create a CSRF token serializer."""
    return URLSafeTimedSerializer(settings.secret_key, salt="csrf-token")


def generate_csrf_token_signed(session_id: str) -> str:
    """Generate a signed CSRF token for a session."""
    serializer = csrf_serializer()
    return serializer.dumps({"session_id": session_id, "token": generate_csrf_token()})


def validate_csrf_token(token: str, session_id: str, max_age: int = 3600) -> bool:
    """Validate a CSRF token."""
    try:
        serializer = csrf_serializer()
        data = serializer.loads(token, max_age=max_age)
        return data.get("session_id") == session_id
    except Exception:
        return False