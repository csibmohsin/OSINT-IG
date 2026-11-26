"""Instagram authentication, session management, client provider, and normalization."""

from osint_ig.instagram.auth import (
    DEFAULT_SESSION_PATH,
    ProviderBackendError,
    get_session_status,
    login_with_credentials,
    resolve_credentials,
    save_session_by_sessionid,
    session_exists,
    verify_session,
)
from osint_ig.instagram.client import InstagramProvider
from osint_ig.instagram.normalizer import normalize_payload

__all__ = [
    "DEFAULT_SESSION_PATH",
    "InstagramProvider",
    "ProviderBackendError",
    "get_session_status",
    "login_with_credentials",
    "normalize_payload",
    "resolve_credentials",
    "save_session_by_sessionid",
    "session_exists",
    "verify_session",
]
