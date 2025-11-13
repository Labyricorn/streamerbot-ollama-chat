from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from twitch_ollama.models import Config


async def get_all(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(Config))
    rows = result.scalars().all()
    return {row.key: row.value for row in rows}


async def get(session: AsyncSession, key: str, default: str | None = None) -> str | None:
    row = await session.get(Config, key)
    return row.value if row else default


async def set(session: AsyncSession, key: str, value: str) -> None:
    row = await session.get(Config, key)
    if row:
        row.value = value
    else:
        session.add(Config(key=key, value=value))
    await session.commit()


async def set_many(session: AsyncSession, mapping: dict[str, str]) -> None:
    for k, v in mapping.items():
        await set(session, k, v)