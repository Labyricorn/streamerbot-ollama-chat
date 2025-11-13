# Design — Libraries and Technology

This document enumerates the concrete technologies and Python libraries used to implement the requirements in `requirements.md`, and explains how each will be applied.

## Runtime and Language
- Python 3.11+: async-friendly runtime for Twitch IO, web server, and LLM calls.
- `asyncio`: built-in event loop, tasks, and `Queue` for job orchestration.

## Twitch Integration
- `twitchio`
  - Purpose: Async Twitch IRC client to connect, join channel, read and post messages.
  - Usage: A bot component registers event handlers for `event_message`, command parsing, and posting responses with rate limits.
  - Requirement mapping: Twitch Bot (listen/persist messages, commands `!ask`, `!filegen`, `!toggle`, etc.), reconnection logic.

## Web Admin Service
- `fastapi`
  - Purpose: HTTP API and server-rendered admin pages via templating.
  - Usage: Define routes for status, config, models, logs, jobs, and files. Pydantic models for input validation.
  - Requirement mapping: Admin UI pages and REST endpoints (Section 7), authentication, CSRF protection integration, and configuration updates.
- `uvicorn`
  - Purpose: ASGI server to run FastAPI.
  - Usage: Development and production server, Windows-friendly.
- `jinja2`
  - Purpose: HTML templating for admin UI pages.
  - Usage: Render dashboard, config forms, logs table, jobs list, file manager, with minimal JS.
- `python-multipart`
  - Purpose: Enable file uploads with `multipart/form-data` in FastAPI.
  - Usage: Handle text file upload on the Files page.
- `aiofiles`
  - Purpose: Async file I/O for uploads and file previews.
  - Usage: Save uploaded files, read file content for previews and generation.
- `itsdangerous`
  - Purpose: Sign and verify CSRF tokens for form posts.
  - Usage: Double-submit cookie pattern with signed tokens; integrated into FastAPI endpoints that mutate state.

## LLM and Ollama Integration
- `httpx`
  - Purpose: Async HTTP client for calling Ollama REST API.
  - Usage: `POST /api/chat` for generation; `GET /api/tags` to list available models; support streaming responses via chunked transfer.
  - Requirement mapping: Prompt assembly and streaming; model enumeration for UI.
- Optional: `tiktoken`
  - Purpose: Token estimation for truncation.
  - Usage: Approximate token budget across models; otherwise fallback to character-length limits.

## Data and Persistence
- `sqlite3` (stdlib) or `SQLAlchemy`
  - Purpose: Storage for configs, chat logs, jobs, and file index.
  - Usage: Simple tables created on startup; queries for pagination and search. If using SQLAlchemy, define declarative models and session management.
  - Requirement mapping: Data Model (configs, chats, jobs, files), persistence for UI and bot state.
- `pydantic` (v2)
  - Purpose: Request/response schemas for FastAPI, validation and serialization.
  - Usage: Define models for configs, logs queries, job requests and results.
- Optional: `pydantic-settings` or `python-dotenv`
  - Purpose: Load typed settings from environment variables.
  - Usage: Secrets (Twitch OAuth token, admin password) and default configuration values.

## Observability and Reliability
- `logging` (stdlib) or `structlog`
  - Purpose: Structured logs for bot events, API calls, errors, and metrics.
  - Usage: JSON or key-value logs; redaction of secrets.
  - Requirement mapping: Error diagnostics, status dashboard, success metrics inputs.

## Testing and Quality
- `pytest`
  - Purpose: Unit and integration tests.
  - Usage: Test prompt assembly, context selection, rate limiting, and API endpoints.
- `pytest-asyncio`
  - Purpose: Async test support for event-driven components.
  - Usage: Simulate Twitch events and Ollama calls.
- `ruff`
  - Purpose: Fast linting.
  - Usage: Enforce code style and catch common issues.
- `mypy` (optional)
  - Purpose: Static type checking.
  - Usage: Validate async flows and data models.

## Component Design and Library Application

### Twitch Bot Service
- Library: `twitchio`
- Responsibilities:
  - Connect using OAuth token; join configured channel.
  - Parse commands with a prefix (configurable), enforce admin-only commands.
  - Persist each message to SQLite and annotate roles (viewer/mod/broadcaster/bot).
  - Enqueue generation jobs via `asyncio.Queue` with metadata (source: chat or file).
  - Rate limiting and cooldowns implemented in-memory: per-channel global cap and per-user cooldown.
  - Reconnect with exponential backoff on disconnect.

### Admin Web Service
- Libraries: `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `aiofiles`, `itsdangerous`, `pydantic`.
- Responsibilities:
  - Render dashboard and forms (Jinja2) for prompt, model, parameters, context policies, rate limits.
  - REST API endpoints for status, config get/set, models, logs (pagination/search), jobs, and files.
  - Authentication: admin password via environment; session cookie for UI; CSRF tokens on state-changing endpoints.
  - File uploads: accept `.txt`, save to uploads directory, index in DB, allow preview, delete.
  - “Send logs to LLM”: POST action that composes a job with recent chats and writes output to jobs.

### LLM Service (Ollama Wrapper)
- Library: `httpx` (or the `ollama` Python client if preferred).
- Responsibilities:
  - Model enumeration via `GET /api/tags` to populate UI.
  - Prompt composition: system prompt + selected chat context + user input/file content.
  - Streaming support: iterate response chunks; buffer or stream to Twitch depending on config.
  - Token budget enforcement: truncate context and input based on configured limits.

### Job Orchestrator
- Library: `asyncio`
- Responsibilities:
  - Maintain `Queue` for generation jobs from bot and web service.
  - Worker task consumes jobs, calls LLM service, writes outputs to DB.
  - Backpressure: check queue depth and surface in dashboard; reject or delay when overloaded.

### Persistence Layer
- Library: `sqlite3` or `SQLAlchemy`
- Tables:
  - `configs`: key/value for runtime settings (system prompt, model, temperature, toggles).
  - `chat_messages`: channel, user, text, role, timestamp.
  - `jobs`: type (chat/file/logs), status, input JSON, output text, timestamps, duration.
  - `files`: name, path, size, timestamp.
- Access Patterns:
  - On startup, ensure tables exist.
  - CRUD operations from bot and web service.
  - Pagination and search with indexed columns (user, ts).

## Security and Safety Controls
- Admin authentication: environment-provided password; hashed in memory with `hashlib` if needed; no storage.
- CSRF: `itsdangerous`-signed tokens; validated on POST.
- Rate limiting: in-memory counters with time windows.
- Sanitization: strip dangerous characters in uploads and inputs; validate file types.
- Secrets: never logged; environment-only access.

## Installation Notes (Informative)
- Core: `fastapi`, `uvicorn`, `twitchio`, `httpx`, `jinja2`, `python-multipart`, `aiofiles`, `pydantic`.
- Data: `SQLAlchemy` (optional; otherwise use `sqlite3`).
- Quality: `pytest`, `pytest-asyncio`, `ruff`, `mypy` (optional).
- Optional: `structlog`, `tiktoken`, `pydantic-settings`.

## Technology Choices Rationale
- Async-first stack (`twitchio`, `fastapi`, `httpx`) aligns with concurrent IO needs.
- FastAPI provides mature validation with Pydantic and easy HTML templating via Jinja2.
- SQLite fits single-user, Windows-friendly deployment with minimal ops.
- In-memory queue is sufficient for single-process; can later move to external queues if scaling.
- Optional libraries allow tuning without overcomplicating MVP.