"""Saved investigation dossiers and target/query history routes."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from osint_ig.api.security import require_local_origin
from osint_ig.database import history_store
from osint_ig.evidence import cases

router = APIRouter()

_HISTORIES = {"targets": history_store.targets, "queries": history_store.queries}


def _history_or_404(kind: str) -> history_store.HistoryStore:
    if kind not in _HISTORIES:
        raise HTTPException(404, f"Unknown history kind: {kind}")
    return _HISTORIES[kind]


@router.get("/api/history/{kind}")
def get_history(kind: str):
    return _history_or_404(kind).list_entries()


@router.delete("/api/history/{kind}")
def delete_history_entry(kind: str, value: str):
    return _history_or_404(kind).remove(value)


@router.post("/api/dossier")
def save_dossier(run: dict, request: Request):
    require_local_origin(request)
    if not run.get("target"):
        raise HTTPException(400, "The investigation is missing its target.")
    return cases.save(run)


@router.get("/api/dossier")
def list_dossiers(request: Request, target: Optional[str] = None):
    require_local_origin(request)
    return cases.list_for(target)


@router.get("/api/dossier/{target}/{dossier_id}")
def get_dossier(target: str, dossier_id: str, request: Request):
    require_local_origin(request)
    run = cases.load(target, dossier_id)
    if run is None:
        raise HTTPException(404, "Investigation not found.")
    return run


@router.delete("/api/dossier/{target}/{dossier_id}")
def delete_dossier(target: str, dossier_id: str, request: Request):
    require_local_origin(request)
    return {"deleted": cases.delete(target, dossier_id)}


@router.get("/api/dossier/{target}/{before_id}/diff/{after_id}")
def diff_dossiers(target: str, before_id: str, after_id: str, request: Request):
    require_local_origin(request)
    before, after = cases.load(target, before_id), cases.load(target, after_id)
    if before is None or after is None:
        raise HTTPException(404, "Investigation not found.")
    if before.get("saved_at", 0) > after.get("saved_at", 0):
        before, after = after, before
    return cases.compare(before, after)
