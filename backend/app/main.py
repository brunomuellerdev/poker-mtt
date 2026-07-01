from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import analytics, auth, hands, marked_hands, tags, tournaments

app = FastAPI(title="Poker MTT API", version="0.4.0")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(tournaments.router, prefix="/api/v1")
app.include_router(marked_hands.router, prefix="/api/v1")
app.include_router(hands.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- serve the built frontend (single-domain deploy) ---------------------
# In production the Vite build is copied to app/static/. When present, mount
# it and fall back to index.html for client-side routes (SPA). API and health
# routes are registered above and take precedence.
_STATIC_DIR = Path(__file__).parent / "static"

if _STATIC_DIR.is_dir():
    _INDEX = _STATIC_DIR / "index.html"

    # hashed assets emitted by Vite under /assets
    app.mount(
        "/assets",
        StaticFiles(directory=_STATIC_DIR / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def _spa_root() -> FileResponse:
        return FileResponse(_INDEX)

    # SPA fallback: any non-API 404 returns index.html so the client router
    # can handle the path (deep links, refresh on /tournaments, etc.)
    @app.exception_handler(StarletteHTTPException)
    async def _spa_fallback(request, exc):  # type: ignore[no-untyped-def]
        if (
            exc.status_code == 404
            and not request.url.path.startswith("/api")
            and request.method == "GET"
        ):
            return FileResponse(_INDEX)
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
