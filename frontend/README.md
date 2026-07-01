# Poker MTT — Frontend (Phase 5)

Vite + React 18 + TypeScript SPA. Dark-theme SaaS layout, TanStack Query for
server state, Zustand for auth/filters, shadcn-style UI primitives (Tailwind +
class-variance-authority).

## Validated

- `npm run typecheck` — passes (strict TS, no errors)
- `npm run build` — production bundle builds clean

> Not browser-tested in this environment (no UI runtime available). The
> guarantee here is "compiles and type-checks", not end-to-end clicked-through.

## Run locally

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api` to the backend at `http://127.0.0.1:8000`
(see vite.config.ts). Start the backend first:

```bash
cd ../backend
. .venv/bin/activate
uvicorn app.main:app --reload
```

Then open http://localhost:5173, register, and you're in.

## Architecture decisions

- Access token in memory (Zustand), never localStorage — limits XSS token theft.
  The refresh token is the backend httpOnly cookie. On load, App calls
  /auth/refresh once to silently restore the session.
- Single-flight refresh (lib/api.ts): concurrent 401s share one refresh call;
  on success the original request replays once, on failure auth state clears.
- Cursor pagination via TanStack useInfiniteQuery; next_cursor feeds
  getNextPageParam; "Load more" appends pages with no overlap.
- TanStack Query owns API state; Zustand holds only token + filters.

## Implemented screens

- Login / Register (auto-login after register)
- Dashboard — summary stat cards
- Tournaments — cursor-paginated table, filters, create dialog, delete

Sessions and Analytics are placeholders; their backend endpoints are live.

## Next phase

Phase 6 — charts (cumulative profit, ROI by category, heatmaps) with Apache
ECharts, wired to /api/v1/analytics.
