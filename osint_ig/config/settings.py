"""Runtime configuration defaults and environment overrides for OSINT IG."""
import os

DEFAULT_SESSION_PATH = os.getenv("OSINT_IG_SESSION_PATH") or os.getenv(
    "INSTAGRAPI_SESSION_FILE", "config/instagrapi_session.json"
)
DEFAULT_CREDENTIALS_PATH = "config/credentials.ini"
DEFAULT_GEMINI_CONFIG_PATH = os.getenv("OSINT_IG_GEMINI_CONFIG", "config/gemini.json")
DEFAULT_CACHE_PATH = os.getenv("OSINT_IG_CACHE_PATH", "cache/requests.sqlite3")
DEFAULT_CACHE_TTL = int(os.getenv("OSINT_IG_CACHE_TTL", "300"))
DEFAULT_DOSSIER_DIR = os.getenv("OSINT_IG_DOSSIER_DIR", "dossier")
DEFAULT_CONTACT_MAX_CHECKS = int(os.getenv("OSINT_IG_CONTACT_MAX_CHECKS", "100"))
DEFAULT_RETRY_ATTEMPTS = max(1, int(os.getenv("OSINT_IG_RETRY_ATTEMPTS", "3")))
DEFAULT_RETRY_DELAY = float(os.getenv("OSINT_IG_RETRY_DELAY", "0.6"))
