# Poker MTT Tracker

Full-stack MTT poker performance analytics.

- `backend/` — FastAPI + SQLAlchemy 2 + PostgreSQL (Phases 0–4)
- `frontend/` — Vite + React + TypeScript SPA (Phase 5)

## Quick start

1. Backend (see `backend/README.md`):
   ```bash
   cd backend
   python -m venv .venv && . .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env          # configure DATABASE_URL + JWT_SECRET
   alembic upgrade head
   uvicorn app.main:app --reload # http://127.0.0.1:8000
   ```
2. Frontend (see `frontend/README.md`):
   ```bash
   cd frontend
   npm install
   npm run dev                   # http://localhost:5173 (proxies /api to backend)
   ```

## Status

| Phase | Scope                                              | State |
| ----- | -------------------------------------------------- | ----- |
| 0     | Foundation, config, Alembic                        | done  |
| 1     | Schema (8 tables, generated columns, constraints)  | done  |
| 2     | Auth (Argon2id, JWT refresh cookie), multi-tenant  | done  |
| 3     | Tournament/Tag CRUD, keyset pagination, metrics    | done  |
| 4     | Analytics (SQL window fns), classification, sessions | done |
| 5     | Frontend scaffold + auth + tournaments CRUD UI     | done  |
| 6     | Charts, dashboards, sessions/analytics UI          | next  |

Backend is validated against PostgreSQL with 45 passing tests. Frontend is
validated to typecheck and build; browser end-to-end testing is done locally.
