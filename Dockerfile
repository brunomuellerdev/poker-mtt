# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React/Vite frontend ----------
FROM node:22-slim AS frontend
WORKDIR /fe

# install deps first (better layer caching)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# build
COPY frontend/ ./
RUN npm run build
# -> produces /fe/dist


# ---------- Stage 2: Python runtime serving API + frontend ----------
FROM python:3.12-slim AS runtime

# psycopg[binary] ships its own libpq, so no system libpq needed.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# install backend (dependencies + app package) from source
COPY backend/ ./
RUN pip install --upgrade pip && pip install .

# copy the built frontend into the location main.py serves from
COPY --from=frontend /fe/dist ./app/static

# Render provides $PORT. Run migrations, then start uvicorn.
# Shell form so $PORT expands and migrations run before the server.
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
