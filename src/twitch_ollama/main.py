from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory

from twitch_ollama.config import settings
from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


def setup_logging() -> None:
    structlog.configure(
        logger_factory=LoggerFactory(),
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )


async def main() -> None:
    setup_logging()
    log = structlog.get_logger()
    log.info("Starting Twitch Ollama Assistant", version="0.1.0")

    await init_db()
    app = create_app()

    log.info("Web server starting", host=settings.host, port=settings.port)
    import uvicorn
    config = uvicorn.Config(app, host=settings.host, port=settings.port, log_config=None)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())