from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from twitch_ollama.config import settings


def test_settings_dirs(tmp_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        settings.uploads_dir = Path(tmp) / "uploads"
        settings.ensure_dirs()
        assert settings.uploads_dir.exists()