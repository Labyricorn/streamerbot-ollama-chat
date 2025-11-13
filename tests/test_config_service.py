from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from twitch_ollama.database import get_session, init_db
from twitch_ollama.models import Config


@pytest.mark.asyncio
async def test_config_crud() -> None:
    await init_db()
    async with get_session() as session:
        await session.run_sync(lambda s: s.query(Config).delete())
        await session.commit()

        from twitch_ollama.services.config import get, set, set_many
        assert await get(session, "test") is None
        await set(session, "test", "value")
        assert await get(session, "test") == "value"
        await set_many(session, {"a": "1", "b": "2"})
        assert await get(session, "a") == "1"
        assert await get(session, "b") == "2"