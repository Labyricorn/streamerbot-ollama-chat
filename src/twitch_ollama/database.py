from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from twitch_ollama.config import settings


class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    global engine, async_session
    engine = create_async_engine(f"sqlite+aiosqlite:///{settings.db_path}", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    if async_session is None:
        raise RuntimeError("Database not initialized")
    async with async_session() as session:
        yield session