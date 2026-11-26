"""Investigation execution, live SSE streaming, cost estimation, cancellation, and cache routes."""
import json
import queue
import threading
import time
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from osint_ig.api.schemas import (
    BaseInvestigationRequest,
    CancelRequest,
    QueryResponse,
    RunRequest,
)
from osint_ig.core.exceptions import (
    CancelledError,
    InvestigationError,
    TargetNotFoundError,
)
from osint_ig.database import history_store
from osint_ig.engine.modules import (
    TARGET_FREE_TOOLS,
    build_tools,
    resolve_call_args,
    tool_specs,
)
from osint_ig.engine.runner import InvestigationRunner
from osint_ig.processing import estimator
from osint_ig.utils.text import normalize_target, sanitize_unicode

router = APIRouter()

TOOL_SPECS = tool_specs()
TOOL_NAMES = {spec["name"] for spec in TOOL_SPECS}
_TOOL_FUNCS = {fn.__name__: fn for fn in build_tools(None)}

_CANCELLATIONS: dict[str, threading.Event] = {}
_CANCELLATIONS_LOCK = threading.Lock()
_SENTINEL = object()


@contextmanager
def _cancellation(run_id: Optional[str]):
    event = threading.Event()
    if run_id:
        with _CANCELLATIONS_LOCK:
            _CANCELLATIONS[run_id] = event
    try:
        yield event
    finally:
        if run_id:
            with _CANCELLATIONS_LOCK:
                _CANCELLATIONS.pop(run_id, None)


def _describe_api_call(method: str, args: tuple, kwargs: dict) -> str:
    parts = []
    if args:
        if "username" in method:
            label = "username"
        elif "by_id" in method:
            label = "id"
        elif "media" in method:
            label = "media_id"
        else:
            label = "user_id"
        parts.append(f"{label}={args[0]}")
    page_id = kwargs.get("page_id") or kwargs.get("next_page_id")
    if page_id:
        parts.append(f"page={page_id}")
    return ", ".join(parts)


def _run_tool_call(name: str, args: dict, fn) -> str:
    return fn(**args) if fn else json.dumps({"error": f"unknown tool {name}"})


def _start_event(service: InvestigationRunner, max_items: Optional[int], cache_ttl_seconds: Optional[int]) -> dict:
    from osint_ig.api import app as app_mod

    service.api.cache_store = app_mod._RAW_CALL_CACHE
    service.api.cache_ttl_seconds = app_mod._resolve_ttl(cache_ttl_seconds)
    service.api.max_calls = max_items
    return {
        "type": "start",
        "target": service.target,
        "target_id": service.target_id,
        "backend": service.backend_name,
        "api_calls_total": service.api_call_count,
    }


def _execute_tool_events(
    service: InvestigationRunner,
    name: str,
    fn,
    raw_args: dict,
    max_items: Optional[int],
    emit_live: Optional[Callable[[dict], None]],
):
    args = resolve_call_args(fn, raw_args, max_items) if fn else raw_args
    yield {"type": "tool_call", "name": name, "input": args}

    api_calls_before = service.api_call_count
    if emit_live:
        service.api.on_call = lambda method, total, cargs, ckwargs, status, error: emit_live(
            {
                "type": "api_call",
                "method": method,
                "total": total,
                "detail": _describe_api_call(method, cargs, ckwargs),
                "status": status,
                "error": error,
            }
        )
    started = time.monotonic()
    try:
        result = _run_tool_call(name, args, fn)
    finally:
        if emit_live:
            service.api.on_call = None
    elapsed_ms = round((time.monotonic() - started) * 1000)
    api_calls_total = service.api_call_count
    try:
        parsed_result = sanitize_unicode(json.loads(result))
    except (TypeError, ValueError):
        parsed_result = result
    is_error = isinstance(parsed_result, dict) and "error" in parsed_result
    yield {
        "type": "tool_result",
        "name": name,
        "result": parsed_result,
        "is_error": is_error,
        "elapsed_ms": elapsed_ms,
        "api_calls_delta": api_calls_total - api_calls_before,
        "api_calls_total": api_calls_total,
    }
    return result, parsed_result, is_error


def _run_direct_events(
    service: InvestigationRunner,
    calls: list,
    max_items: Optional[int] = None,
    cache_ttl_seconds: Optional[int] = None,
    emit_live: Optional[Callable[[dict], None]] = None,
):
    yield _start_event(service, max_items, cache_ttl_seconds)

    dispatch = {fn.__name__: fn for fn in build_tools(service)}
    for call in calls:
        yield from _execute_tool_events(service, call.name, dispatch.get(call.name), call.args, max_items, emit_live)


def _run_safe_events(make_events: Callable[[Callable[[dict], None]], Iterator[dict]]):
    q: "queue.Queue[dict]" = queue.Queue()

    def worker():
        try:
            for event in make_events(q.put):
                q.put(event)
        except CancelledError:
            pass
        except Exception as exc:
            q.put({"type": "error", "detail": f"Investigation error: {exc}"})
        finally:
            q.put(_SENTINEL)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        item = q.get()
        if item is _SENTINEL:
            return
        yield item


def _sse(event: dict) -> str:
    return f"data: {json.dumps(sanitize_unicode(event), ensure_ascii=False, default=str)}\n\n"


def _build_runner_or_http_error(target: Optional[str]) -> InvestigationRunner:
    from osint_ig.api import app as app_mod

    try:
        service = app_mod.build_runner(target)
    except TargetNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except InvestigationError as exc:
        raise HTTPException(502, str(exc)) from exc
    if target:
        history_store.targets.record(service.user.get("username") or target)
    return service


def _respond(req: BaseInvestigationRequest, service: InvestigationRunner, make_events):
    if req.verbose:
        def stream():
            with _cancellation(req.run_id) as cancelled:
                service.api.cancelled = cancelled
                yield ":" + " " * 2048 + "\n\n"
                try:
                    for event in _run_safe_events(make_events):
                        yield _sse(event)
                finally:
                    cancelled.set()

        return StreamingResponse(stream(), media_type="text/event-stream")

    answer = ""
    tool_calls: list = []
    error_detail = None
    with _cancellation(req.run_id) as cancelled:
        service.api.cancelled = cancelled
        for event in _run_safe_events(make_events):
            if event["type"] == "tool_call":
                tool_calls.append({"name": event["name"], "input": event["input"]})
            elif event["type"] == "tool_result":
                for tc in reversed(tool_calls):
                    if tc["name"] == event["name"] and "result" not in tc:
                        tc["result"] = event["result"]
                        tc["is_error"] = event["is_error"]
                        tc["elapsed_ms"] = event["elapsed_ms"]
                        tc["api_calls_delta"] = event["api_calls_delta"]
                        break
            elif event["type"] == "answer":
                answer = event["text"]
            elif event["type"] == "error":
                error_detail = event["detail"]

    if error_detail is not None:
        raise HTTPException(502, error_detail)

    return QueryResponse(
        target=req.target,
        target_id=service.target_id,
        backend=service.backend_name,
        api_calls_total=service.api_call_count,
        answer=answer,
        tool_calls=tool_calls,
    )


@router.delete("/api/cache")
def clear_cache():
    from osint_ig.api import app as app_mod

    raw_cache = app_mod._RAW_CALL_CACHE
    cleared = len(raw_cache) if isinstance(raw_cache, dict) else raw_cache.clear()
    if isinstance(raw_cache, dict):
        raw_cache.clear()
    return {"cleared": cleared}


@router.post("/api/run", response_model=QueryResponse)
def run(req: RunRequest):
    if not req.calls:
        raise HTTPException(400, "Select at least one investigation module.")
    unknown = sorted({call.name for call in req.calls} - TOOL_NAMES)
    if unknown:
        raise HTTPException(400, f"Unknown module: {', '.join(unknown)}")
    needs_target = [c.name for c in req.calls if c.name not in TARGET_FREE_TOOLS]
    target = normalize_target(req.target)
    if needs_target and not target:
        raise HTTPException(400, f"A target username is required for: {', '.join(sorted(set(needs_target)))}")
    service = _build_runner_or_http_error(target if needs_target else None)
    return _respond(
        req,
        service,
        lambda emit_live: _run_direct_events(
            service, req.calls, max_items=req.max_items, cache_ttl_seconds=req.cache_ttl_seconds, emit_live=emit_live
        ),
    )


@router.post("/api/estimate")
def estimate_cost(req: RunRequest):
    from osint_ig.api import app as app_mod

    if not req.calls:
        raise HTTPException(400, "Select at least one module.")
    target = normalize_target(req.target)
    service = _build_runner_or_http_error(target)
    service.api.cache_store = app_mod._RAW_CALL_CACHE
    service.api.cache_ttl_seconds = app_mod._resolve_ttl(req.cache_ttl_seconds)
    calls = [
        {"name": c.name, "args": resolve_call_args(_TOOL_FUNCS.get(c.name), c.args, req.max_items)}
        for c in req.calls
    ]
    result = estimator.estimate(calls, service.user, req.max_items)
    result["profile"] = {
        "media_count": service.user.get("media_count"),
        "follower_count": service.user.get("follower_count"),
        "following_count": service.user.get("following_count"),
    }
    return result


@router.post("/api/cancel")
def cancel(req: CancelRequest):
    with _CANCELLATIONS_LOCK:
        event = _CANCELLATIONS.get(req.run_id)
    if event is not None:
        event.set()
    return {"cancelled": event is not None}
