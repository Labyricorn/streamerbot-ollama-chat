from __future__ import annotations

import httpx
import structlog

from twitch_ollama.config import settings

log = structlog.get_logger()


async def list_models() -> list[str]:
    try:
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=5) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        log.error("Failed to list Ollama models", error=e)
        return []