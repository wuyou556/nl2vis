# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NL2VIS (ChatChart) — a Natural Language to Visualization platform. Users upload data files, describe analysis needs in natural language, and the system generates visualizations via a ReAct Agent with Docker-sandboxed code execution.

**Current state**: Early-stage. Database models and sandbox are implemented; the Agent core, API routes, services, schemas, and frontend are scaffolded but not yet built.

## Tech Stack

| Layer    | Technology                             |
| -------- | -------------------------------------- |
| Frontend | Vue 3 + TypeScript + Vite + ECharts    |
| Backend  | FastAPI + SQLAlchemy (async) + Celery  |
| Agent    | LangChain / ReAct pattern (planned)    |
| Sandbox  | Flask + subprocess + Docker isolation  |
| Database | PostgreSQL 16                          |
| Cache    | Redis 7                                |
| Deploy   | Docker Compose                         |

## Commands

```bash
# Start all infrastructure (PostgreSQL, Redis, Sandbox)
docker-compose up -d

# Backend dev server
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend dev server (scaffolded, no source yet)
cd frontend
npm install && npm run dev

# Sandbox dev server
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

- **Single `.env`** at the project root (`nl2vis-platform/.env`), loaded by both `backend/app/main.py` and `backend/alembic/env.py`
- `DEBUG=true` sets wide-open CORS; `DEBUG=false` restricts to `ALLOWED_ORIGINS`
- `DATABASE_URL` uses `postgresql+asyncpg://` for runtime (async), but Alembic swaps it to `postgresql+psycopg2://` (sync) internally

### Database Layer (`backend/app/db/`)

- `base.py` — shared `DeclarativeBase` class for all models
- `session.py` — async engine via `create_async_engine`, `AsyncSessionLocal` factory, and `get_db()` dependency generator with auto-commit/rollback

### Models (`backend/app/models/`)

Four tables, all imported in `__init__.py` for Alembic autogenerate:

- **User** — `id`, `username`, `email`, `hashed_password`, `is_active` — has many Sessions
- **Session** — `id`, `user_id` (FK), `title`, `started_at`, `ended_at`, `status` — has many Messages
- **Message** — `id`, `session_id` (FK), `sender` (user/agent/system), `content` — belongs to Session
- **File** — `id`, `user_id` (FK nullable), `filename`, `storage_path`, `content_type`, `size`, `uploaded_at`
- `TimestampMixin` provides `created_at` + `updated_at` on User, Session, File

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
  db/              # Base model + async session
  models/          # SQLAlchemy ORM models (User, Session, Message, File)
  agent/           # (scaffold) tools/, prompts/, memory/ — all empty
  api/v1/          # (scaffold) routes — empty
  schemas/         # (scaffold) Pydantic models — empty
  services/        # (scaffold) business logic — empty
  tasks/           # (scaffold) Celery tasks — empty
  core/            # (scaffold) cross-cutting concerns — empty
  utils/           # (scaffold) helpers — empty
backend/tests/     # empty
frontend/src/      # scaffolded directory, no source files yet
```

## Migrations (Alembic)

- Config: `backend/alembic.ini` + `backend/alembic/env.py`
- `env.py` manually loads `.env` from project root and converts `asyncpg` → `psycopg2` for migration operations
- All models must be imported in `backend/app/models/__init__.py` for autogenerate to detect them
- Always run alembic commands from the `backend/` directory
