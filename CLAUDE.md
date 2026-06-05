# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NL2VIS (ChatChart) — a Natural Language to Visualization platform. Users upload data files, describe analysis needs in natural language, and the system generates visualizations via a ReAct Agent with Docker-sandboxed code execution.

**Current state**: Backend is fully functional (database, API routes, Agent core, service layer). Frontend is not yet started. Celery and tests are still empty scaffolds.

## Tech Stack

| Layer    | Technology                               |
| -------- | ---------------------------------------- |
| Frontend | Vue 3 + TypeScript + Vite + ECharts      |
| Backend  | FastAPI + SQLAlchemy (async)             |
| Agent    | ReAct pattern (custom, vanilla Python)   |
| Sandbox  | Flask + subprocess + Docker isolation    |
| Database | PostgreSQL 16                            |
| Cache    | Redis 7                                  |
| Deploy   | Docker Compose                           |

## Commands

```bash
# Start all infrastructure (PostgreSQL, Redis, Sandbox)
docker-compose up -d

# Backend dev server
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend dev server (not yet started)
cd frontend
npm install && npm run dev

# Sandbox dev server (if running standalone, not in Docker)
cd sandbox
pip install -r requirements.txt
python executor_api.py

# Alembic migrations (run from backend/ directory)
cd backend
alembic revision --autogenerate -m "description"   # create migration
alembic upgrade head                                # apply migrations
alembic downgrade -1                                # rollback one step
alembic history                                     # view migration history
```

## Architecture

### Environment & Config

- **Single `.env`** at the project root (`nl2vis-platform/.env`), loaded by `backend/app/main.py` and `backend/alembic/env.py`
- `DEBUG=true` sets wide-open CORS; `DEBUG=false` restricts to `ALLOWED_ORIGINS`
- `DATABASE_URL` uses `postgresql+asyncpg://` for runtime (async), but Alembic swaps it to `postgresql+psycopg2://` (sync) internally
- LLM config: `LLM_MODEL_NAME`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`
- Agent behavior: `AGENT_MAX_ITERATIONS`, `AGENT_TOOL_TIMEOUT`, `AGENT_VERBOSE`, `SANDBOX_URL`

### Database Layer (`backend/app/db/`)

- `base.py` — shared `DeclarativeBase` class for all models
- `session.py` — async engine via `create_async_engine`, `AsyncSessionLocal` factory, and `get_db()` dependency generator with auto-commit/rollback

### Models (`backend/app/models/`)

Four tables, all imported in `__init__.py` for Alembic autogenerate:

- **User** — `id`, `username`, `email`, `hashed_password`, `is_active` — has many Sessions
- **Session** — `id`, `user_id` (FK), `title`, `started_at`, `ended_at`, `status` — has many Messages and Files
- **Message** — `id`, `session_id` (FK), `sender` (user/agent/system), `content` — belongs to Session
- **File** — `id`, `session_id` (FK), `filename`, `storage_path`, `content_type`, `size`, `uploaded_at`
- `TimestampMixin` provides `created_at` + `updated_at` on User, Session, File

### API Routes (`backend/app/api/v1/`)

- **`auth.py`** — `/auth/register`, `/auth/login`, `/auth/me` — JWT-based authentication with bcrypt
- **`sessions.py`** — Full CRUD for sessions, messages (with Agent integration), and file uploads
- **`users.py`** — User profile endpoints
- **`router.py`** — Aggregates all routers under `/api/v1` prefix

### Agent Core (`backend/app/agent/`)

Custom ReAct Agent built with vanilla Python (no LangChain dependency):

```
agent/
├── __init__.py              # Public API: AgentExecutor, AgentSettings, etc.
├── schemas.py               # 4 dataclasses: AgentAction, AgentObservation,
│                            #   AgentStep, AgentResult
├── config.py                # AgentSettings dataclass + get_agent_config() factory
│                            #   + create_llm_client() (OpenAI-compatible SDK)
├── prompts.py               # System prompt template with tools_description placeholder
├── memory.py                # ConversationMemory: load_history, truncate (sliding
│                            #   window), build_messages (role mapping agent→assistant)
├── core.py                  # AgentExecutor: ReAct loop (Think→Act→Observe),
│                            #   _parse_llm_output() with regex, _call_tool() with
│                            #   graceful degradation
└── tools/
    ├── __init__.py           # TOOL_REGISTRY dict, get_tools(), build_tools_description()
    ├── base.py               # BaseTool ABC with @abstractmethod name/description/run
    ├── file_reader.py        # Read CSV/Excel/JSON files (MAX_ROWS=50 defense)
    ├── data_preview.py       # Structured preview: shape, dtypes, head, describe, missing
    └── code_executor.py      # POST code to Docker sandbox via httpx; constructor injection
```

**ReAct Loop**: `run()` assembles context (system prompt + history + user message), then iterates: LLM call → regex parse → if Action: call tool + append observation → if Final Answer: return AgentResult. Max iterations enforced with fallback timeout message.

**Error Strategy**: Tools return `[错误]`-prefixed strings instead of throwing. AgentExecutor has 3-layer fault tolerance: unknown tool → tool exception → unknown exception. Service layer catches remaining failures and stores `sender="system"` messages.

### Service Layer (`backend/app/services/`)

Thin business-logic layer between routes and Agent:

- **`session_service.py`** — `SessionService.process_message()`: queries files + history, assembles AgentExecutor, bridges sync Agent via `asyncio.to_thread()`, saves Agent reply
- **`__init__.py`** — Exports `SessionService`

### Sandbox (`sandbox/`)

Flask server running in a Docker container (`python:3.11-slim`):

- **`POST /execute`** — writes code to a temp `.py` file, runs with `subprocess.run()`, returns `{stdout, stderr, exit_code, truncated}`. Timeout capped at 120s, output truncated at `EXECUTOR_MAX_OUTPUT` (default 64KB)
- **`GET /health`** — health check
- Security: runs as non-root `sandbox` user, container receives `--network=none`, `--memory=512m`, `--read-only` in production

### Docker Compose

Three services: `postgres` (16-alpine), `redis` (7-alpine), `sandbox` (custom build). All have health checks. Shared network: `nl2vis-network`.

### Directory Map

```
backend/app/
  main.py          # FastAPI app creation, CORS, env loading
  db/              # base.py + session.py (async engine)
  models/          # User, Session, Message, File + TimestampMixin
  agent/           # ReAct Agent core (schemas, config, prompts, memory, core, tools/)
  api/v1/          # auth, sessions, users routes + router aggregator
  schemas/         # Pydantic: user, session, message, file
  services/        # SessionService (business orchestration)
  core/            # config.py (JWT settings, etc.)
  tasks/           # (empty scaffold) Celery tasks
  utils/           # (empty scaffold) helpers
backend/tests/     # (empty scaffold)
frontend/src/      # (empty scaffold)
```

### Data Flow (Send Message)

```
POST /api/v1/sessions/{id}/messages
  → sessions.py: save Message(sender="user")
  → SessionService.process_message()
    → query files + history from DB
    → assemble AgentExecutor(llm, tools, memory, settings)
    → await asyncio.to_thread(executor.run, ...)
      → AgentExecutor ReAct loop
        → LLM API call → parse → tool call → observe → repeat
      → return AgentResult(output="...")
    → save Message(sender="agent", content=result.output)
  → return agent Message to frontend
```

## Migrations (Alembic)

- Config: `backend/alembic.ini` + `backend/alembic/env.py`
- `env.py` manually loads `.env` from project root and converts `asyncpg` → `psycopg2` for migration operations
- All models must be imported in `backend/app/models/__init__.py` for autogenerate to detect them
- Always run alembic commands from the `backend/` directory
