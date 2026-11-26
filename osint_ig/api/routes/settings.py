"""Instagram connection settings and optional Google Gemini AI routes."""
from fastapi import APIRouter, HTTPException, Request

from osint_ig.ai import gemini_analyzer
from osint_ig.api.schemas import (
    CredentialsRequest,
    GeminiAnalyzeRequest,
    GeminiConfigRequest,
    GeminiVerifyRequest,
    SessionIdRequest,
)
from osint_ig.api.security import require_local_origin
from osint_ig.instagram.auth import ProviderBackendError

router = APIRouter()


@router.get("/api/settings/instagram")
def instagram_settings(request: Request):
    from osint_ig.api import app as app_mod

    require_local_origin(request)
    return app_mod.get_session_status()


@router.post("/api/settings/instagram/session")
def set_instagram_session(req: SessionIdRequest, request: Request):
    from osint_ig.api import app as app_mod

    require_local_origin(request)
    try:
        result = app_mod.save_session_by_sessionid(req.sessionid)
        return {**app_mod.get_session_status(), **result}
    except ProviderBackendError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/settings/instagram/credentials")
def set_instagram_credentials(req: CredentialsRequest, request: Request):
    from osint_ig.api import app as app_mod

    require_local_origin(request)
    try:
        result = app_mod.login_with_credentials(req.username, req.password)
        return {**app_mod.get_session_status(), **result}
    except ProviderBackendError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/settings/instagram/verify")
def verify_instagram_session(request: Request):
    from osint_ig.api import app as app_mod

    require_local_origin(request)
    try:
        result = app_mod.verify_session()
        return {**app_mod.get_session_status(), **result}
    except ProviderBackendError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/api/ai/config")
def get_ai_config(request: Request):
    require_local_origin(request)
    return gemini_analyzer.get_config_state()


@router.post("/api/ai/config")
def save_ai_config(req: GeminiConfigRequest, request: Request):
    require_local_origin(request)
    return gemini_analyzer.save_config(api_key=req.api_key, model=req.model, enabled=req.enabled)


@router.post("/api/ai/verify")
def verify_ai_config(req: GeminiVerifyRequest, request: Request):
    require_local_origin(request)
    try:
        return gemini_analyzer.verify_connection(api_key=req.api_key, model=req.model)
    except gemini_analyzer.GeminiConfigError as exc:
        raise HTTPException(400, str(exc)) from exc
    except gemini_analyzer.GeminiAPIError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/api/ai/analyze")
def analyze_with_gemini(req: GeminiAnalyzeRequest, request: Request):
    require_local_origin(request)
    try:
        return gemini_analyzer.analyze_investigation(
            target=req.target,
            results=req.results,
            analysis_type=req.analysis_type,
            question=req.question,
        )
    except gemini_analyzer.GeminiConfigError as exc:
        raise HTTPException(400, str(exc)) from exc
    except gemini_analyzer.GeminiAPIError as exc:
        raise HTTPException(502, str(exc)) from exc
