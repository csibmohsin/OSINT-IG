"""Optional Google Gemini API integration for post-collection OSINT analysis.

Strictly post-collection: Gemini only analyzes data already gathered by
OsintgramService. Core investigation functionality never depends on Gemini.
API keys are stored server-side only (env var GEMINI_API_KEY or config/gemini.json)
and are never exposed in responses, logs, or frontend code.
"""
import json
import os
from pathlib import Path
from typing import Optional

from osint_ig.utils.text import mask_secret as mask_token

GEMINI_CONFIG_PATH = Path(os.getenv("OSINT_IG_GEMINI_CONFIG", "config/gemini.json"))

SUPPORTED_MODELS = [
    {"id": "gemini-4-hydrogen", "label": "Gemini 4 Hydrogen (Balanced, Recommended)"},
    {"id": "gemini-4-argon", "label": "Gemini 4 Argon (Fast Reasoning)"},
    {"id": "gemini-4-neon", "label": "Gemini 4 Neon (Frontier)"},
    {"id": "gemini-4-carbon", "label": "Gemini 4 Carbon (Deep Reasoning)"},
    {"id": "gemini-3.5-flash-lite", "label": "Gemini 3.5 Flash-Lite (Ultra-Fast)"},
]
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-4-hydrogen")

ANALYSIS_TYPES = {
    "profile_summary": "Provide a structured Profile Summary based strictly on the collected profile and account metadata.",
    "investigation_summary": "Provide a comprehensive Investigation Summary synthesizing all collected modules.",
    "hashtag_analysis": "Analyze the collected hashtags, themes, frequency distribution, and topical focus.",
    "engagement_analysis": "Analyze public engagement metrics (likes, comments, frequent commenters, ratios) from the collected data.",
    "posting_pattern": "Analyze posting cadence, active hours/weekdays, and temporal patterns from the collected timestamps.",
    "content_categorization": "Categorize the target's content types, captions, media formats, and recurring subjects.",
    "relationship_summary": "Summarize observed network relationships (followers, followings, mutuals, tagged users, frequent commenters).",
    "evidence_report": "Draft a formal CSIB evidence-based intelligence assessment summarizing all observed findings and provenance.",
    "qa": "Answer the investigator's specific question using only the collected investigation records.",
}

_FORENSIC_SYSTEM_PROMPT = """You are an OSINT Intelligence Analyst assisting an investigator on the OSINT IG platform (CSIB).

STRICT ANALYTICAL RULES:
1. Analyze ONLY the collected investigation records provided in the prompt.
2. NEVER invent, extrapolate, or fabricate missing data, usernames, dates, locations, or relationships.
3. NEVER claim an association or intent without direct supporting evidence in the records.
4. Reference the source command name (e.g., [get_user_info], [get_hashtags]) for observed facts.
5. Structure your analysis into these exact four sections using Markdown headings:
   ### Observed Facts
   ### Derived Statistics
   ### AI Interpretations
   ### Unknown or Unavailable Information
"""


class GeminiConfigError(Exception):
    """Raised when Gemini is not configured or disabled."""


class GeminiAPIError(Exception):
    """Raised when a Gemini API call fails."""


def _load_file_config(config_path: Optional[Path] = None) -> dict:
    path = config_path or GEMINI_CONFIG_PATH
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, ValueError):
        pass
    return {}


def _save_file_config(data: dict, config_path: Optional[Path] = None) -> None:
    path = config_path or GEMINI_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.json")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def get_config_state(config_path: Optional[Path] = None) -> dict:
    """Return safe configuration state (never exposes the raw API key)."""
    env_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    file_cfg = _load_file_config(config_path)
    file_key = (file_cfg.get("api_key") or "").strip()

    if env_key:
        active_key = env_key
        source = "env"
        locked = True
    elif file_key:
        active_key = file_key
        source = "file"
        locked = False
    else:
        active_key = ""
        source = None
        locked = False

    model = (os.getenv("GEMINI_MODEL") or file_cfg.get("model") or DEFAULT_MODEL).strip()
    enabled = bool(file_cfg.get("enabled", True)) and bool(active_key)

    return {
        "configured": bool(active_key),
        "enabled": enabled,
        "model": model,
        "source": source,
        "locked": locked,
        "preview": mask_token(active_key) if active_key else None,
        "supported_models": SUPPORTED_MODELS,
    }


def save_config(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    enabled: Optional[bool] = None,
    config_path: Optional[Path] = None,
) -> dict:
    """Persist Gemini configuration server-side."""
    current = _load_file_config(config_path)
    if api_key is not None:
        cleaned = api_key.strip()
        if cleaned:
            current["api_key"] = cleaned
        elif api_key == "":
            current.pop("api_key", None)
    if model is not None and model.strip():
        current["model"] = model.strip()
    if enabled is not None:
        current["enabled"] = bool(enabled)
    _save_file_config(current, config_path)
    return get_config_state(config_path)


def _resolve_active_key_and_model(
    api_key_override: Optional[str] = None,
    model_override: Optional[str] = None,
    config_path: Optional[Path] = None,
) -> tuple[str, str]:
    env_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    file_cfg = _load_file_config(config_path)
    key = (api_key_override or "").strip() or env_key or (file_cfg.get("api_key") or "").strip()
    model = (
        (model_override or "").strip()
        or (os.getenv("GEMINI_MODEL") or "").strip()
        or (file_cfg.get("model") or "").strip()
        or DEFAULT_MODEL
    )
    return key, model


def _make_client(api_key: str):
    from google import genai

    return genai.Client(api_key=api_key)


def verify_connection(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config_path: Optional[Path] = None,
) -> dict:
    """Verify Gemini API connectivity with a minimal non-stored interaction."""
    key, resolved_model = _resolve_active_key_and_model(api_key, model, config_path)
    if not key:
        raise GeminiConfigError("No Gemini API key provided or configured.")
    try:
        client = _make_client(key)
        interaction = client.interactions.create(
            model=resolved_model,
            input="Reply with OK.",
            store=False,
        )
        return {
            "ok": True,
            "model": resolved_model,
            "response": (interaction.output_text or "OK").strip()[:100],
        }
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "API key not valid" in msg:
            raise GeminiAPIError(
                "Invalid Gemini API key. Please enter a valid key from Google AI Studio in Settings -> AI Configuration."
            ) from e
        raise GeminiAPIError(f"Gemini verification failed: {e}") from e


def _prepare_evidence_payload(results: list, max_chars: int = 24000) -> str:
    """Compact collected results for prompt context while preserving provenance."""
    compact = []
    for item in results or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "unknown")
        res = item.get("result")
        if isinstance(res, dict):
            res = {k: v for k, v in res.items() if k not in ("previews", "timestamps")}
        if isinstance(res, list) and len(res) > 50:
            res = {"total_count": len(res), "sample_first_50": res[:50]}
        compact.append({"command": name, "is_error": bool(item.get("is_error")), "data": res})
    text = json.dumps(compact, ensure_ascii=False, default=str)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n... [truncated due to context size]"
    return text


def analyze_investigation(
    target: Optional[str],
    results: list,
    analysis_type: str = "investigation_summary",
    question: Optional[str] = None,
    config_path: Optional[Path] = None,
) -> dict:
    """Run post-collection Gemini analysis on already-gathered investigation results."""
    state = get_config_state(config_path)
    if not state["configured"]:
        raise GeminiConfigError("Gemini API is not configured. Configure it in Settings -> AI Configuration.")
    if not state["enabled"]:
        raise GeminiConfigError("Gemini AI Analysis is currently disabled in Settings -> AI Configuration.")

    key, model = _resolve_active_key_and_model(config_path=config_path)
    task_instruction = ANALYSIS_TYPES.get(analysis_type, ANALYSIS_TYPES["investigation_summary"])
    if analysis_type == "qa":
        q = (question or "").strip()
        if not q:
            raise GeminiConfigError("Please enter a question about the collected results.")
        task_instruction = f"Investigator Question: {q}\n\n{task_instruction}"

    evidence = _prepare_evidence_payload(results)
    prompt = (
        f"Target Account: {target or 'N/A (target-free search)'}\n"
        f"Analysis Task: {task_instruction}\n\n"
        f"Collected Investigation Records (JSON):\n{evidence}"
    )

    try:
        client = _make_client(key)
        interaction = client.interactions.create(
            model=model,
            input=prompt,
            system_instruction=_FORENSIC_SYSTEM_PROMPT,
            store=False,
        )
        return {
            "target": target,
            "analysis_type": analysis_type,
            "model": model,
            "analysis": (interaction.output_text or "").strip(),
        }
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "API key not valid" in msg:
            raise GeminiAPIError(
                "Invalid Gemini API key. Please enter a valid key from Google AI Studio in Settings -> AI Configuration."
            ) from e
        raise GeminiAPIError(f"Gemini analysis failed: {e}") from e
