"""Text normalization, secret masking, and Unicode sanitization helpers."""
import re
from typing import Optional


def sanitize_unicode(value):
    """Neutralize unpaired UTF-16 surrogates occasionally present in Instagram payloads."""
    if isinstance(value, str):
        return value.encode("utf-8", "replace").decode("utf-8")
    if isinstance(value, dict):
        return {k: sanitize_unicode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_unicode(v) for v in value]
    return value


def mask_secret(value: Optional[str]) -> Optional[str]:
    """Return a non-reversible masked preview (e.g. ``AIza…9876``) for UI display."""
    if not value:
        return None
    s = str(value).strip()
    if len(s) <= 8:
        return s[:1] + "…" + s[-1:] if len(s) >= 2 else "…"
    return f"{s[:4]}…{s[-4:]}"


def normalize_target(raw: Optional[str]) -> Optional[str]:
    """Extract a clean Instagram username from a handle or profile URL."""
    val = (raw or "").strip()
    if not val:
        return None
    match = re.match(r"^https?://(?:www\.)?instagram\.com/([^/?#]+)", val, re.I)
    if match:
        val = match.group(1)
    return val.lstrip("@").strip() or None
