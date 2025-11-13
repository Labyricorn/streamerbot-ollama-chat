# Product Requirements Document — Twitch ↔ Ollama Assistant

## 1. Overview
The project connects a Twitch channel to a local Ollama LLM instance. Broadcasters and moderators can configure behavior via a web UI, log and search chat, and generate LLM responses from live chat context or from a local text file. The system prioritizes safety, configurability, and reliable operation on Windows.

### Objectives
- Provide an interactive assistant that responds to chat-triggered commands.
- Offer an admin HTML page to configure prompts, models, and policies.
- Log chat with search/export; optionally send logs as context to the LLM.
- Generate messages based on a selected or uploaded text file.
- Maintain rate limits and moderation controls to prevent spam/abuse.

### Scope
- Twitch IRC chat integration for one channel.
- Local Ollama integration for chat-based and file-based prompt flows.
- Admin web UI with configuration, logging, job monitoring, and file handling.

### Out of Scope (Initial Release)
- Multi-channel management.
- Cloud deployment and horizontal scaling.
- Advanced moderation (ML toxicity detection).

## 2. Users and Roles
- Broadcaster/Admin: Full control via admin UI and privileged chat commands.
- Moderators: Limited privileged commands to operate the bot in chat.
- Viewers: Use public commands when allowed; read bot responses.

## 3. Key Use Cases
- Configure system prompt, model, and response policies via UI.
- Trigger LLM responses from chat using commands (e.g., `!ask`).
- Send recent chat logs to the LLM for summarization/analysis.
- Upload or select a text file and generate a message from its contents.
- View chat logs and generation jobs; search and export data.
- Enforce rate limits, cooldowns, and safe message length.

## 4. Functional Requirements

### 4.1 Twitch Bot
- Connect to Twitch via OAuth token and join the configured channel.
- Listen to chat messages and persist them with metadata (user, roles, time).
- Support commands (configurable prefixes and enable/disable):
  - `!ask <question>`: Generate an answer using configured context policy.
  - `!filegen <filename>`: Generate answer from selected file content.
  - `!context <N>`: Use last N messages as context for the next generation.
  - `!toggle on|off`: Enable/disable bot responding in chat.
  - `!status`: Show current model, rate limits, and queue depth.
  - `!help`: Show available commands and basic usage.
- Admin-only commands (broadcaster/mods):
  - `!setprompt <text>`: Update the system prompt.
  - `!model <name>`: Switch model to an available Ollama model.
  - `!cooldown <seconds>` / `!ratelimit <N>`: Update runtime limits.
- Rate limiting and safety:
  - Global max responses per minute.
  - Per-user cooldown.
  - Message length cap and multi-part continuation rules.
  - Keyword-trigger mode optional; default is commands-only.
- Posting policy:
  - Buffered posting (default) or streaming partial lines (configurable).

### 4.2 Admin Web UI
- Authentication with admin password (session cookie) and CSRF protection.
- Dashboard: connection status, active model, queue depth, recent errors.
- Configuration page:
  - System prompt editor (multi-line text).
  - Model selector (populated from Ollama models).
  - Parameters: temperature, max tokens, streaming toggle.
  - Context policy: last N messages or time window; role filters.
  - Trigger policy: commands-only vs. keyword mode; blocked terms list.
  - Rate limit and cooldown settings.
- Logs page: paginated chat table with search and export (CSV/JSON).
- Jobs page: list of LLM generations with inputs, outputs, status, timing.
- Files page: upload text files, list, preview, delete, and “Generate from file”.
- Action: “Send logs to LLM” to summarize or analyze recent chat.

### 4.3 LLM/Ollama Integration
- Enumerate models from local Ollama to populate UI selectors.
- Compose prompts: system prompt + curated chat context + user/file input.
- Support streaming at the HTTP layer; Twitch posting mode configurable.
- Enforce token budget with truncation and optional pre-summarization.

### 4.4 Chat Logging and Context
- Persist every message with metadata: channel, user, text, badges/roles, timestamp.
- Context builder options:
  - Window by count (last N) or time (last T minutes).
  - Role filtering (exclude bot/self where appropriate).
  - Sanitization and truncation to fit token budget.
- Export logs as CSV/JSON from UI.

### 4.5 File-Based Generation
- Upload text files via UI; store locally and index in DB.
- Select file for generation; preview content before use.
- Optional chunking/summarization for large files.
- Posting destination: UI-only or post to Twitch (default off, admin toggle).

### 4.6 Configuration and Persistence
- Environment variables for secrets: Twitch OAuth token, admin password.
- Persist runtime settings in SQLite `configs` table.
- Changes through UI take effect immediately and survive restarts.

## 5. Non-Functional Requirements
- Reliability: bot reconnects to Twitch on disconnect; retry Ollama on transient errors.
- Performance: typical generation <10s; UI responsive under 100ms for config/log queries.
- Security: no secrets in logs; CSRF protection; input sanitization; role checks for admin-only actions.
- Compatibility: Windows-first; single-binary or simple `uvicorn` run; no complex system dependencies.
- Observability: structured logs, error traces, and basic metrics (responses/minute, queue depth).

## 6. System Architecture
- Runtime: `asyncio` to unify Twitch IO, web server, and LLM requests.
- Services:
  - Twitch Bot service: IRC client, command parsing, message posting with rate limits.
  - Web Admin service: REST API and HTML pages.
  - LLM service: Ollama wrapper with streaming support.
  - Job Worker: `asyncio.Queue` consumer for generation tasks.
- Data:
  - SQLite for configs, chats, and jobs.
  - Local file storage for uploads.

## 7. API Endpoints (Admin Service)
- `GET /api/status`: connection state, model, queue depth.
- `GET /api/config`: return current configuration.
- `POST /api/config`: update configuration (authenticated, CSRF-protected).
- `GET /api/models`: list available Ollama models.
- `GET /api/logs`: paginated chat logs; filters for user/time.
- `POST /api/logs/send`: send recent logs to LLM for summary/analysis.
- `GET /api/jobs`: paginated job list.
- `POST /api/jobs/ask`: enqueue a chat-based generation.
- `POST /api/jobs/file`: enqueue a file-based generation.
- `POST /api/files`: upload a text file.
- `GET /api/files`: list files; `GET /api/files/{id}`: preview.
- `DELETE /api/files/{id}`: delete file.

## 8. Data Model (SQLite)
- `configs(key TEXT PRIMARY KEY, value TEXT)`
- `chat_messages(id INTEGER PK, channel TEXT, user TEXT, text TEXT, role TEXT, ts DATETIME)`
- `jobs(id INTEGER PK, type TEXT, status TEXT, input_json TEXT, output_text TEXT, ts DATETIME, duration_ms INT)`
- `files(id INTEGER PK, name TEXT, path TEXT, size INT, ts DATETIME)`

## 9. Rate Limiting and Moderation
- Global responses per minute threshold (configurable).
- Per-user cooldown seconds (configurable).
- Blocked terms filter for inputs and outputs.
- Max Twitch message length with continuation policy.

## 10. Error Handling and Fallbacks
- Twitch reconnect with backoff on disconnects.
- Ollama request retries with capped attempts.
- Graceful degradation: post “busy” or “error” messages in chat when needed.
- Detailed error logs (without secrets) and surfaced in UI.

## 11. Deployment and Operations
- Prerequisites: Python 3.11+, Ollama installed and running locally; Twitch OAuth token.
- Windows: run as a single process or two processes (bot + web) with shared DB.
- Configuration via environment variables and persisted DB settings.
- Backup strategy: periodic export of SQLite DB and uploads folder.

## 12. Success Metrics
- Time-to-response and success rate of generations.
- Admin UI latency and reliability.
- Rate limit violations avoided; minimal moderation incidents.
- User engagement: number of successful `!ask` commands per stream.

## 13. Risks and Mitigations
- Overload from spam commands → strict rate limits and admin toggles.
- Large context causing slow responses → truncation and summarization.
- Local Ollama model quality varies → allow easy model switching and parameter tuning.
- Windows-specific issues (network, file paths) → testing and simplified dependencies.

## 14. Milestones
- MVP:
  - Twitch bot with `!ask`, `!filegen`, `!toggle`.
  - Admin UI: prompt, model, basic parameters; logs view; file upload.
  - SQLite persistence; basic rate limiting; buffered posting.
- Beta:
  - Streaming responses; advanced context policies; jobs dashboard.
  - Export logs; keyword mode; blocked terms; error dashboard.
  - Summarization pipeline for large files and contexts.

## 15. Acceptance Criteria
- Bot connects to the configured Twitch channel and responds to commands.
- Admin UI edits system prompt, model, and parameters; changes take effect immediately.
- Chat logs persisted, searchable, and exportable.
- File upload and file-based generation works; result visible in jobs and optionally posted.
- Rate limits/cooldowns prevent spam; admin-only actions are restricted.
- No secrets in logs; CSRF and session-based auth enforced.