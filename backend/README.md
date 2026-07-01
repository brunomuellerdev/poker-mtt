# Poker MTT — Backend

Performance analytics for poker MTTs. Phase 0 (foundation) + Phase 1 (schema) +
Phase 2 (auth & multi-tenant) — validated against PostgreSQL 16.

## Run the API

```bash
cd backend
. .venv/bin/activate
uvicorn app.main:app --reload
# docs at http://127.0.0.1:8000/docs
```

## Auth (Phase 2)

| Method | Path                    | Purpose                                  |
| ------ | ----------------------- | ---------------------------------------- |
| POST   | `/api/v1/auth/register` | create user + settings + seed eval bands |
| POST   | `/api/v1/auth/login`    | returns access token; sets refresh cookie|
| POST   | `/api/v1/auth/refresh`  | new access token from httpOnly cookie    |
| POST   | `/api/v1/auth/logout`   | clears refresh cookie                    |
| GET    | `/api/v1/auth/me`       | current user (requires Bearer token)     |

- **Argon2id** password hashing (`argon2-cffi` defaults), auto-rehash on login
  when parameters change.
- **Access token** returned in the response body (Bearer); **refresh token** in
  an httpOnly cookie scoped to `/auth` — mitigates XSS token theft in SPAs.
  Toggle `COOKIE_SECURE=true` behind HTTPS.
- Token `type` claim is enforced: an access token cannot be used at `/refresh`.
- Email is normalized to lowercase; duplicate registration → 409.
- Login verifies a dummy hash for unknown emails to keep timing uniform against
  account enumeration.
- On registration, `UserSettings` and the default `EvaluationRange` bands (ROI,
  ITM, final-table %, win %, reliability — from spec) are seeded in one
  transaction. Users edit their own bands later; nothing is hardcoded.
- `JWT_SECRET` left at its default with `DEBUG=false` aborts startup
  (config validator) — prevents shipping the public placeholder secret.

## Stack

- Python 3.12+ (target 3.13; validated on 3.12)
- FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, pydantic-settings
- PostgreSQL 16+ (uses generated columns, CHECK constraints, window-function-ready indexes)
- psycopg 3 driver

## Setup

```bash
cd backend
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env            # edit DATABASE_URL / JWT_SECRET
```

`.env` requires a running Postgres. Default DSN:

```
DATABASE_URL=postgresql+psycopg://poker:poker@localhost:5432/poker_mtt
```

Create the DB and role:

```bash
createdb poker_mtt
psql -c "CREATE ROLE poker WITH LOGIN PASSWORD 'poker'; ALTER DATABASE poker_mtt OWNER TO poker;"
```

## Migrations

```bash
alembic upgrade head      # apply schema
alembic downgrade base    # tear down (reversible)
alembic check             # verify models == migration (no drift)
```

To regenerate after model changes:

```bash
alembic revision --autogenerate -m "describe change"
# ALWAYS review the generated file before applying — autogenerate does
# not diff generated/Computed columns and may miss CHECK edits.
alembic upgrade head
```

## Schema notes (design decisions)

- **Money stored native + `fx_rate_to_base` (default 1.0).** `profit_base` is a
  generated column = native profit × fx. Single-currency users never touch fx.
- **Cost is correct for rebuys/re-entries:**
  `total_cost = buy_in*(1+rebuys+reentries) + addon_cost`. Add-ons priced
  separately (`addon_cost`), not as buy-in multiples.
- **Derived flags are generated columns** (`profit_native`, `profit_base`,
  `itm`, `winner`, `final_table`, `total_cost`) — indexable, no drift.
- **Tournament taxonomy split into orthogonal axes:** `speed`, `entry_structure`,
  `bounty_type` (replaces the overlapping `format`/`tournament_type` enums).
- **Enums are VARCHAR + CHECK on enum values** (lowercase), not native PG ENUM —
  cheap to evolve. Storage and CHECK both use `.value` via `values_callable`.
- **`ix_tournaments_order (user_id, date, start_time, id)`** gives deterministic
  ordering for accumulated profit, drawdown, and streak window functions.
- **`EvaluationRange`** is a generic per-user, per-indicator band table
  (`indicator_key`, `range_order`, `[lower, upper)`) — new indicators reuse it
  with no schema change.

## Layout

```
backend/
├── app/
│   ├── config.py           # pydantic-settings
│   ├── db/
│   │   ├── base.py         # Base + UUID/Timestamp mixins
│   │   ├── enums.py        # domain enums
│   │   ├── models.py       # ORM models (Phase 1)
│   │   ├── metadata.py     # aggregates models for Alembic
│   │   └── session.py      # engine + SessionLocal + get_db
│   ├── api/v1/             # (Phase 3) routers
│   ├── repositories/       # (Phase 3) data access
│   ├── services/           # (Phase 3) business logic
│   ├── schemas/            # (Phase 3) Pydantic I/O
│   ├── core/metrics/       # (Phase 3) pure calculation engine
│   └── tests/
├── alembic/                # env.py wired to app settings + Base.metadata
├── alembic.ini
└── pyproject.toml
```

## Known follow-ups

- `updated_at` uses ORM-side `onupdate`; add a `BEFORE UPDATE` trigger if writes
  will bypass the ORM.
- `final_table_size` defaults to 9; service layer (Phase 2) should set it from
  `table_size` on insert when the table is not full-ring.
- Default `EvaluationRange` seed runs at user creation (Phase 2), not in a
  migration (per-user data, not schema).

## Next phase

Phase 3 — Tournament / Session / Tag CRUD (multi-tenant, every query scoped to
`user_id`) and the **pure calculation engine** (`app/core/metrics/`): profit with
rebuys, ROI, ITM%, streaks, drawdown — with unit tests before any dashboard.
Service layer will set `final_table_size` from `table_size` on insert.
