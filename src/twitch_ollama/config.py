from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    twitch_oauth_token: str = Field(..., description="OAuth token for Twitch IRC")
    twitch_channel: str = Field(..., description="Channel to join")
    admin_password: str = Field(..., description="Admin UI password")
    ollama_base_url: str = Field("http://localhost:11434", description="Ollama API base URL")

    db_path: Path = Field(Path("data.db"), description="SQLite database file")
    uploads_dir: Path = Field(Path("uploads"), description="Directory for uploaded text files")

    host: str = Field("127.0.0.1", description="FastAPI host")
    port: int = Field(8000, description="FastAPI port")

    log_level: str = Field("INFO", description="Logging level")
    secret_key: str = Field("change-me-in-production", description="Secret key for CSRF protection and sessions")

    def ensure_dirs(self) -> None:
        """Create uploads directory if missing."""
        self.uploads_dir.mkdir(exist_ok=True)


settings = Settings()
settings.ensure_dirs()