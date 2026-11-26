"""Localhost-only origin guard for sensitive configuration and evidence routes."""
from fastapi import HTTPException, Request

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1", "0.0.0.0"}


def is_local_host(value: str) -> bool:
    host = (value or "").strip().lower()
    if host.startswith("http://") or host.startswith("https://"):
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0]
    if not host.startswith("[") and host.count(":") == 1:
        host = host.rsplit(":", 1)[0]
    elif host.startswith("["):
        host = host.split("]", 1)[0] + "]"
    return host in _LOCAL_HOSTS


def require_local_origin(request: Request) -> None:
    """Reject requests whose Host or Origin header points outside localhost."""
    if not is_local_host(request.headers.get("host", "")):
        raise HTTPException(403, "This endpoint only answers requests reached via localhost.")
    origin = request.headers.get("origin")
    if origin and not is_local_host(origin):
        raise HTTPException(403, "Origin not allowed.")
