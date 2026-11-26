"""OSINT IG — FastAPI Application Factory.

Serves the modular API routers and the local-first forensic frontend from ``frontend/``.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from osint_ig.api.routes import cases, dashboard, exports, investigations, settings
from osint_ig.database.request_cache import RequestCache
from osint_ig.engine.runner import build_runner  # noqa: F401 (re-exported for route/test patching)
from osint_ig.instagram.auth import (  # noqa: F401 (re-exported for route/test patching)
    get_session_status,
    login_with_credentials,
    save_session_by_sessionid,
    verify_session,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

DEFAULT_CACHE_TTL_SECONDS = int(os.getenv("OSINT_IG_CACHE_TTL", "300"))
CACHE_PATH = os.getenv("OSINT_IG_CACHE_PATH", "cache/requests.sqlite3")
_RAW_CALL_CACHE = RequestCache(Path(CACHE_PATH)) if CACHE_PATH else {}


def _resolve_ttl(ttl_seconds: Optional[int]) -> int:
    return DEFAULT_CACHE_TTL_SECONDS if ttl_seconds is None else ttl_seconds


app = FastAPI(title="OSINT IG")

app.include_router(dashboard.router)
app.include_router(investigations.router)
app.include_router(settings.router)
app.include_router(cases.router)
app.include_router(exports.router)


@app.middleware("http")
async def _security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
