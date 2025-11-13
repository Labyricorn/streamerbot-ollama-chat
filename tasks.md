# Tasks — Ordered from Easiest to Hardest

Each task lists sub-tasks and references to the relevant sections in `requirements.md` and the design elements in `design.md`.

## 1) Project scaffolding and environment setup (Easy)
- Sub-tasks:
  - Initialize Python 3.11 project structure
  - Create base settings loader from environment variables
  - Add dependency pins
- Requirements refs: 11 Deployment and Operations
- Design refs: Runtime and Language; Installation Notes

## 2) SQLite schema initialization (Easy)
- Sub-tasks:
  - Create tables: `configs`, `chat_messages`, `jobs`, `files`
  - On startup, migrate/ensure tables exist
- Requirements refs: 8 Data Model; 4.6 Configuration and Persistence
- Design refs: Data and Persistence (sqlite3/SQLAlchemy)

## 3) FastAPI app skeleton and Jinja2 base templates (Easy)
- Sub-tasks:
  - Initialize FastAPI app and mount admin routes
  - Add Jinja2 environment and base layout
- Requirements refs: 4.2 Admin Web UI; 7 API Endpoints
- Design refs: Web Admin Service (fastapi, jinja2, uvicorn)

## 4) Status endpoint and dashboard stub (Easy)
- Sub-tasks:
  - Implement `GET /api/status` with placeholder values
  - Render dashboard page consuming status
- Requirements refs: 7 API Endpoints; 4.2 Admin Web UI (Dashboard)
- Design refs: Web Admin Service; Observability and Reliability

## 5) Config endpoints and UI form (Easy)
- Sub-tasks:
  - Implement `GET/POST /api/config` (system prompt, model, parameters)
  - Jinja2 page for editing configuration
- Requirements refs: 4.2 Configuration page; 4.6 Configuration and Persistence; 7 API Endpoints
- Design refs: Web Admin Service; Pydantic models; Data and Persistence

## 6) Admin authentication and CSRF protection (Easy→Medium)
- Sub-tasks:
  - Add session-based admin login with password from env
  - Integrate CSRF tokens on mutating endpoints
- Requirements refs: 4.2 Admin Web UI (Authentication, CSRF); 5 Non-Functional (Security)
- Design refs: Web Admin Service; Security and Safety Controls (itsdangerous)

## 7) Ollama model enumeration (Easy)
- Sub-tasks:
  - Implement `GET /api/models` calling Ollama `GET /api/tags`
  - Populate model selector in UI
- Requirements refs: 4.3 LLM/Ollama Integration; 7 API Endpoints
- Design refs: LLM Service (httpx)

## 8) File uploads and management UI (Easy→Medium)
- Sub-tasks:
  - Implement `POST /api/files`, `GET /api/files`, `GET /api/files/{id}`, `DELETE /api/files/{id}`
  - Store files on disk and index in DB; preview page
- Requirements refs: 4.5 File-Based Generation; 7 API Endpoints; 8 Data Model
- Design refs: Web Admin Service (python-multipart, aiofiles); Persistence Layer

## 9) Chat logs API and UI (Medium)
- Sub-tasks:
  - Implement `GET /api/logs` with pagination and search
  - Render paginated logs page; add export CSV/JSON
- Requirements refs: 4.4 Chat Logging and Context; 7 API Endpoints
- Design refs: Web Admin Service; Data and Persistence; Observability

## 10) Job list API and UI (Medium)
- Sub-tasks:
  - Implement `GET /api/jobs` and display recent jobs
  - Show inputs, outputs, status, timestamps, duration
- Requirements refs: 7 API Endpoints; 3 Key Use Cases (monitor generations)
- Design refs: Web Admin Service; Persistence Layer

## 11) Job orchestrator using asyncio.Queue (Medium)
- Sub-tasks:
  - Create in-memory queue for generation jobs
  - Implement worker consuming queue; write outputs to DB
- Requirements refs: 6 System Architecture (Job Worker); 4.3 LLM/Ollama Integration
- Design refs: Runtime and Language (asyncio); Job Orchestrator

## 12) Prompt composer and context builder (Medium)
- Sub-tasks:
  - Build prompt: system prompt + curated chat context + user/file input
  - Implement context windowing by count/time, role filters, sanitization, truncation
- Requirements refs: 4.3 LLM/Ollama Integration; 4.4 Chat Logging and Context
- Design refs: LLM Service; Optional tiktoken; Persistence Layer

## 13) Twitch bot connection and basic command parsing (Medium)
- Sub-tasks:
  - Connect to Twitch with OAuth; join channel
  - Parse commands with prefix; identify admin/mod roles
- Requirements refs: 4.1 Twitch Bot (connect, commands); 5 Non-Functional (Reliability)
- Design refs: Twitch Integration (twitchio)

## 14) Persist incoming chat messages (Medium)
- Sub-tasks:
  - Store each message with user, role, timestamp
  - Avoid duplicates and label bot’s own messages
- Requirements refs: 4.4 Chat Logging; 8 Data Model
- Design refs: Persistence Layer; Twitch Integration

## 15) Implement `!ask` flow with buffered posting (Medium→Hard)
- Sub-tasks:
  - Enqueue chat-based job from bot command
  - Worker calls Ollama; bot posts final message within length limits
- Requirements refs: 4.1 Twitch Bot (commands); 4.3 LLM/Ollama; 9 Rate Limiting and Moderation (length cap)
- Design refs: Twitch Integration; Job Orchestrator; LLM Service

## 16) Implement “Send logs to LLM” action (Medium→Hard)
- Sub-tasks:
  - Admin UI button calling `POST /api/logs/send`
  - Compose context; store summary/analysis in jobs
- Requirements refs: 4.2 Admin Web UI (Action); 4.4 Chat Logging and Context
- Design refs: Web Admin Service; LLM Service; Persistence Layer

## 17) Rate limiting and cooldown controls (Hard)
- Sub-tasks:
  - Global responses-per-minute limit; per-user cooldown
  - Surface limits in status; enforce in bot before posting
- Requirements refs: 9 Rate Limiting and Moderation; 4.1 Twitch Bot (Safety)
- Design refs: Security and Safety Controls; Twitch Integration

## 18) File-based generation command and UI (Hard)
- Sub-tasks:
  - Implement `POST /api/jobs/file` and `!filegen <filename>`
  - Read file content; compose prompt; post result or keep UI-only
- Requirements refs: 4.5 File-Based Generation; 7 API Endpoints; 3 Key Use Cases
- Design refs: Web Admin Service; LLM Service; Persistence Layer

## 19) Streaming response handling (Hard)
- Sub-tasks:
  - Support streaming from Ollama (chunked)
  - Configurable Twitch posting: buffered vs. partial updates
- Requirements refs: 4.3 LLM/Ollama Integration (Streaming); 4.1 Twitch Bot (Posting policy)
- Design refs: LLM Service (httpx streaming); Twitch Integration

## 20) Keyword trigger mode and blocked terms filter (Hard)
- Sub-tasks:
  - Optional keyword triggers with cooldowns
  - Input/output filtering for blocked terms
- Requirements refs: 4.1 Twitch Bot (Trigger policy, Safety filters); 9 Rate Limiting and Moderation
- Design refs: Security and Safety Controls; Twitch Integration

## 21) Error handling, retries, and reconnect logic (Hard)
- Sub-tasks:
  - Twitch reconnect with backoff; Ollama retry with caps
  - Graceful fallback messages; error logging in UI
- Requirements refs: 10 Error Handling and Fallbacks; 5 Non-Functional (Reliability)
- Design refs: Observability and Reliability; Twitch Integration; LLM Service

## 22) Dashboards and metrics surfacing (Hard)
- Sub-tasks:
  - Show queue depth, responses/min, last errors on dashboard
  - Structured logs for diagnostics
- Requirements refs: 4.2 Admin Web UI (Dashboard); 12 Success Metrics
- Design refs: Observability (logging/structlog); Web Admin Service

## 23) Large file/context summarization (Hardest)
- Sub-tasks:
  - Chunk large inputs; pre-summarize before generation
  - Ensure token budget compliance; configurable thresholds
- Requirements refs: 4.5 File-Based Generation (Optional chunking/summarization); 4.4 Chat Logging (Truncation)
- Design refs: LLM Service; Optional tiktoken; Prompt Composer