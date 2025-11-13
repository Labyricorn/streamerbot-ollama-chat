from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from twitch_ollama.config import settings
from twitch_ollama.database import get_session
from twitch_ollama.routers import admin, api
from twitch_ollama.services import jobs


def create_app() -> FastAPI:
    app = FastAPI(title="Twitch Ollama Assistant", version="0.1.0")

    # Create uploads directory if it doesn't exist
    uploads_path = Path(settings.uploads_dir)
    uploads_path.mkdir(parents=True, exist_ok=True)

    # Serve uploads as static files
    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")

    # Templates
    templates = Jinja2Templates(directory="src/twitch_ollama/templates")
    app.state.templates = templates

    # Include routers
    app.include_router(api.router, prefix="/api")
    app.include_router(admin.router, prefix="/admin")

    # Startup: init job queue worker
    @app.on_event("startup")
    async def startup() -> None:
        await jobs.start_worker()

    # Shutdown: stop worker
    @app.on_event("shutdown")
    async def shutdown() -> None:
        await jobs.stop_worker()

    return app