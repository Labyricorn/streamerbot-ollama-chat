from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from twitch_ollama.database import Base


class Config(Base):
    __tablename__ = "configs"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String)
    user: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String)
    ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    input_json: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(Integer)
    ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())