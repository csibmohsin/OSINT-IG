"""Dashboard, system metadata, and intelligence module catalog routes."""
from importlib import metadata

from fastapi import APIRouter, Request

import osint_ig as pkg_meta
from osint_ig.ai import gemini_analyzer
from osint_ig.api.security import require_local_origin
from osint_ig.database import history_store
from osint_ig.engine.modules import tool_specs
from osint_ig.evidence import cases

router = APIRouter()

THIRD_PARTY = [
    ("fastapi", "Web API framework", "https://fastapi.tiangolo.com"),
    ("uvicorn", "ASGI server", "https://www.uvicorn.org"),
    ("pydantic", "Data validation", "https://docs.pydantic.dev"),
    ("instagrapi", "Instagram data provider", "https://github.com/subzeroid/instagrapi"),
    ("google-genai", "Optional Gemini AI analysis", "https://ai.google.dev"),
    ("geopy", "Reverse geocoding (Nominatim)", "https://github.com/geopy/geopy"),
]


def _library_credit(dist: str, role: str, url: str) -> dict:
    try:
        meta = metadata.metadata(dist)
    except metadata.PackageNotFoundError:
        return {"name": dist, "role": role, "url": url, "version": None, "license": None}
    license_ = meta.get("License-Expression") or meta.get("License") or ""
    if not license_ or len(license_) > 40:
        classifiers = [c for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
        license_ = classifiers[0].split(" :: ")[-1] if classifiers else None
    return {"name": dist, "role": role, "url": url, "version": meta["Version"], "license": license_}


@router.get("/api/about")
def about():
    return {
        "product_name": pkg_meta.__product__,
        "tagline": pkg_meta.__tagline__,
        "version": pkg_meta.__version__,
        "author": pkg_meta.__author__,
        "organization": pkg_meta.__organization__,
        "organization_full": pkg_meta.__organization_full__,
        "libraries": [_library_credit(*lib) for lib in THIRD_PARTY],
    }


@router.get("/api/dashboard")
def dashboard(request: Request):
    """Return real backend statistics and recent activity for the Dashboard."""
    from osint_ig.api import app as app_mod

    require_local_origin(request)
    dossiers = cases.list_for()
    targets_hist = history_store.targets.list_entries()
    ig_status = app_mod.get_session_status()
    ai_status = gemini_analyzer.get_config_state()
    raw_cache = app_mod._RAW_CALL_CACHE
    cache_entries = len(raw_cache) if isinstance(raw_cache, dict) else 0
    return {
        "stats": {
            "total_investigations": len(dossiers),
            "completed_investigations": len(dossiers),
            "saved_reports": len(dossiers),
            "recent_targets_count": len(targets_hist),
        },
        "recent_investigations": dossiers[:8],
        "recent_targets": targets_hist[:8],
        "instagram_status": ig_status,
        "ai_status": {
            "configured": ai_status["configured"],
            "enabled": ai_status["enabled"],
            "model": ai_status["model"],
        },
        "cache_entries": cache_entries,
    }


@router.get("/api/tools")
def list_tools():
    return tool_specs()
