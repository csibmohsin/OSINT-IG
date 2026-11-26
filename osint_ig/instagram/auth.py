"""Instagram session & credential authentication for OSINT IG."""
import configparser
import json
import os
from pathlib import Path
from typing import Optional

from osint_ig.config.settings import DEFAULT_CREDENTIALS_PATH, DEFAULT_SESSION_PATH
from osint_ig.core.exceptions import ProviderError


class ProviderBackendError(ProviderError):
    """Raised when the Instagram provider cannot authenticate or verify a session."""


def resolve_credentials(
    credentials_path: str = DEFAULT_CREDENTIALS_PATH,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve (username, password) from env vars first, then config/credentials.ini."""
    username = os.getenv("OSINT_IG_USERNAME") or os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("OSINT_IG_PASSWORD") or os.getenv("INSTAGRAM_PASSWORD")
    if username and password:
        return username, password
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(credentials_path)
        username = username or parser.get("Credentials", "username", fallback=None) or None
        password = password or parser.get("Credentials", "password", fallback=None) or None
    except Exception:
        pass
    return username, password


def session_exists(session_path: str = DEFAULT_SESSION_PATH) -> bool:
    """Return True if a persisted Instagram session file exists."""
    return Path(session_path).exists()


def get_session_status(
    session_path: str = DEFAULT_SESSION_PATH,
    credentials_path: str = DEFAULT_CREDENTIALS_PATH,
) -> dict:
    """Return safe, non-sensitive status metadata for the local Instagram session."""
    sf = Path(session_path)
    exists = sf.exists()
    username, password = resolve_credentials(credentials_path)
    session_user_id = None
    if exists:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            auth_data = data.get("authorization_data") or {}
            session_user_id = auth_data.get("ds_user_id") or data.get("user_id")
        except Exception:
            pass
    return {
        "backend": "instagrapi",
        "session_exists": exists,
        "connected": bool(exists and session_user_id),
        "username": username,
        "user_id": str(session_user_id) if session_user_id else None,
        "credentials_configured": bool(username and password),
    }


def save_session_by_sessionid(
    sessionid: str,
    session_path: str = DEFAULT_SESSION_PATH,
) -> dict:
    """Authenticate via browser ``sessionid`` cookie and persist to ``session_path``."""
    sid = (sessionid or "").strip()
    if not sid:
        raise ProviderBackendError("Session ID is required.")
    from instagrapi import Client

    cl = Client()
    try:
        cl.login_by_sessionid(sid)
        out = Path(session_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        cl.dump_settings(out)
        return {"connected": True, "username": cl.username, "user_id": str(cl.user_id)}
    except Exception as exc:
        raise ProviderBackendError(f"Session login failed: {exc}") from exc


def login_with_credentials(
    username: str,
    password: str,
    session_path: str = DEFAULT_SESSION_PATH,
    credentials_path: str = DEFAULT_CREDENTIALS_PATH,
) -> dict:
    """Persist username/password to ``credentials.ini`` and attempt direct login."""
    uname = (username or "").strip().lstrip("@")
    pwd = password or ""
    if not uname or not pwd:
        raise ProviderBackendError("Both Instagram username and password are required.")

    parser = configparser.ConfigParser(interpolation=None)
    if Path(credentials_path).exists():
        parser.read(credentials_path)
    if not parser.has_section("Credentials"):
        parser.add_section("Credentials")
    parser.set("Credentials", "username", uname)
    parser.set("Credentials", "password", pwd)
    cred_file = Path(credentials_path)
    cred_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cred_file, "w", encoding="utf-8") as handle:
        parser.write(handle)
    try:
        os.chmod(cred_file, 0o600)
    except OSError:
        pass

    from instagrapi import Client

    cl = Client()
    try:
        cl.login(uname, pwd)
        out = Path(session_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        cl.dump_settings(out)
        return {"connected": True, "username": cl.username or uname, "user_id": str(cl.user_id)}
    except Exception as exc:
        raise ProviderBackendError(
            f"Credentials saved, but Instagram login failed: {exc}. "
            "If Instagram blocks direct login or asks for 2FA, use a browser Session ID below."
        ) from exc


def verify_session(
    session_path: str = DEFAULT_SESSION_PATH,
    credentials_path: str = DEFAULT_CREDENTIALS_PATH,
) -> dict:
    """Verify that the saved Instagram session is active and responsive."""
    from osint_ig.instagram.client import InstagramProvider

    if not session_exists(session_path):
        raise ProviderBackendError("No saved Instagram session found.")
    username, password = resolve_credentials(credentials_path)
    provider = InstagramProvider(username or "", password or "", session_path=session_path)
    try:
        info = provider._cl.account_info()
        return {
            "connected": True,
            "username": getattr(info, "username", username),
            "user_id": str(getattr(info, "pk", "")),
        }
    except Exception as exc:
        raise ProviderBackendError(f"Session verification failed: {exc}") from exc
