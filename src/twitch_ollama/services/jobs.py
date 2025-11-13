from __future__ import annotations

import asyncio
from typing import Any

import structlog

log = structlog.get_logger()

_queue: asyncio.Queue[Any] | None = None
_worker_task: asyncio.Task[None] | None = None


async def start_worker() -> None:
    global _queue, _worker_task
    _queue = asyncio.Queue(maxsize=1000)
    _worker_task = asyncio.create_task(_worker())
    log.info("Job worker started")


async def stop_worker() -> None:
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    log.info("Job worker stopped")


async def enqueue(job: Any) -> None:
    if _queue is None:
        raise RuntimeError("Worker not started")
    await _queue.put(job)


async def _worker() -> None:
    log.info("Worker loop started")
    while True:
        try:
            job = await _queue.get()
            log.info("Processing job", job=job)
            # Placeholder: actual LLM call will be added later
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            log.info("Worker cancelled")
            break
        except Exception as e:
            log.error("Worker error", error=e)