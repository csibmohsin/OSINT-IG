"""Tests for the OSINT IG FastAPI web layer, driven through a fake service."""
import time
import types

import pytest
from fastapi.testclient import TestClient

import osint_ig.api.app as appmod
import osint_ig.database.history_store as history


@pytest.fixture
def client(tmp_path, monkeypatch):
    history.targets.path = tmp_path / "targets.json"
    history.queries.path = tmp_path / "queries.json"

    class FakeApi:
        cache_store = cache_ttl_seconds = max_calls = on_call = None

    def fake_build(target):
        if target == "nobody":
            raise appmod.TargetNotFoundError("@nobody not found")
        return types.SimpleNamespace(
            api=FakeApi(),
            target=target,
            target_id=1 if target else None,
            backend_name="instagrapi",
            api_call_count=0,
            user={"username": target.lstrip("@").lower()} if target else {},
            get_user_info=lambda **k: {"follower_count": 10},
            get_media_type=lambda **k: {"photos": 1, "previews": [{"id": "x", "media_url": "u"}]},
            search_hashtag=lambda **k: {"hashtag": "#milano", "posts": 0, "authors": [], "previews": []},
            search_location=lambda **k: {"place": None, "posts": 0, "authors": [], "previews": []},
        )

    monkeypatch.setattr(appmod, "build_runner", fake_build)
    return TestClient(appmod.app, base_url="http://127.0.0.1:8000")


def test_frontend_routes_load(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "OSINT IG" in r.text
    assert "Osintgram" not in r.text
    assert client.get("/styles/main.css").status_code == 200
    assert client.get("/js/app.js").status_code == 200


def test_tools_endpoint_lists_commands(client):
    specs = client.get("/api/tools").json()
    names = {s["name"] for s in specs}
    assert {"get_user_info", "get_media_type", "compare_with", "get_highlights"} <= names
    compare = next(s for s in specs if s["name"] == "compare_with")
    assert {p["name"] for p in compare["params"]} == {"other_username", "scope", "limit"}
    scope = next(p for p in compare["params"] if p["name"] == "scope")
    assert scope["choices"] == ["both", "followers", "followings"]


def test_run_executes_selected_commands_in_order(client):
    r = client.post("/api/run", json={"target": "alice", "calls": [
        {"name": "get_user_info"}, {"name": "get_media_type"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == ""
    assert [c["name"] for c in body["tool_calls"]] == ["get_user_info", "get_media_type"]


def test_run_accepts_instagram_profile_url(client):
    r = client.post("/api/run", json={"target": "https://www.instagram.com/alice/?hl=en", "calls": [
        {"name": "get_user_info"}]})
    assert r.status_code == 200
    assert [e["value"] for e in client.get("/api/history/targets").json()] == ["alice"]


def test_search_commands_run_without_a_target(client, monkeypatch):
    built = []

    def fake_build(target):
        built.append(target)

        class FakeApi:
            cache_store = cache_ttl_seconds = max_calls = on_call = cancelled = None

        return types.SimpleNamespace(
            api=FakeApi(), target=target, target_id=None, backend_name="instagrapi", api_call_count=0, user={},
            search_hashtag=lambda **k: {"hashtag": "#milano", "posts": 0, "authors": [], "previews": []})

    monkeypatch.setattr(appmod, "build_runner", fake_build)
    r = client.post("/api/run", json={"calls": [{"name": "search_hashtag", "args": {"hashtag": "milano"}}]})
    assert r.status_code == 200
    assert built == [None]
    assert client.get("/api/history/targets").json() == []


def test_target_still_required_for_target_commands(client):
    r = client.post("/api/run", json={"calls": [{"name": "get_user_info"}]})
    assert r.status_code == 400
    assert "get_user_info" in r.json()["detail"]


def test_download_endpoint_rejects_non_cdn_urls(client):
    r = client.post("/api/download", json={"urls": ["https://evil.com/x.jpg"], "name": "x"})
    assert r.status_code == 400


def test_run_rejects_empty_and_unknown(client):
    assert client.post("/api/run", json={"target": "a", "calls": []}).status_code == 400
    assert client.post("/api/run", json={"target": "a", "calls": [{"name": "__init__"}]}).status_code == 400


def test_history_delete_and_unknown_kind(client):
    client.post("/api/run", json={"target": "alice", "calls": [{"name": "get_user_info"}]})
    assert client.delete("/api/history/targets", params={"value": "alice"}).json() == []
    assert client.get("/api/history/nope").status_code == 404


def test_cancel_endpoint_stops_a_running_search(tmp_path, monkeypatch):
    import threading
    import osint_ig.engine.runner as svcmod

    history.targets.path = tmp_path / "t.json"
    history.queries.path = tmp_path / "q.json"
    running = threading.Event()
    calls = []

    class FakeApi:
        cache_store = cache_ttl_seconds = max_calls = on_call = None
        cancelled = None

    api = FakeApi()

    def slow_tool(**kwargs):
        running.set()
        for _ in range(1000):
            if api.cancelled is not None and api.cancelled.is_set():
                raise svcmod.CancelledError("stopped")
            calls.append(1)
            time.sleep(0.005)
        return {"done": True}

    monkeypatch.setattr(appmod, "build_runner", lambda target: types.SimpleNamespace(
        api=api, target=target, target_id=1, backend_name="instagrapi", api_call_count=len(calls),
        user={"username": target}, get_user_info=slow_tool))

    client = TestClient(appmod.app)
    result = {}

    def run():
        result["response"] = client.post(
            "/api/run", json={"target": "a", "run_id": "run-1", "calls": [{"name": "get_user_info"}]})

    worker = threading.Thread(target=run)
    worker.start()
    assert running.wait(timeout=5)
    time.sleep(0.05)
    assert client.post("/api/cancel", json={"run_id": "run-1"}).json() == {"cancelled": True}
    worker.join(timeout=5)
    assert not worker.is_alive()

    spent_at_cancel = len(calls)
    time.sleep(0.1)
    assert len(calls) == spent_at_cancel
    assert len(calls) < 1000


def test_estimate_endpoint(client, monkeypatch):
    def fake_build(target):
        class FakeApi:
            cache_store = cache_ttl_seconds = max_calls = on_call = cancelled = None
        return types.SimpleNamespace(
            api=FakeApi(), target=target, target_id=1, backend_name="instagrapi", api_call_count=1,
            user={"username": target, "media_count": 60, "follower_count": 500, "following_count": 100})

    monkeypatch.setattr(appmod, "build_runner", fake_build)
    r = client.post("/api/estimate", json={"target": "a", "calls": [
        {"name": "get_user_info"}, {"name": "get_followers", "args": {"limit": 100}}]})
    assert r.status_code == 200
    data = r.json()
    assert data["total_high"] >= data["total_low"] > 0
    assert [c["name"] for c in data["per_command"]] == ["get_user_info", "get_followers"]
    assert data["profile"]["follower_count"] == 500


def test_estimate_requires_commands(client):
    assert client.post("/api/estimate", json={"target": "a", "calls": []}).status_code == 400


def test_cancel_unknown_run_is_harmless(client):
    assert client.post("/api/cancel", json={"run_id": "nope"}).json() == {"cancelled": False}


def test_dossier_save_list_open_diff_delete(client, tmp_path, monkeypatch):
    from osint_ig.evidence import cases as dossier
    monkeypatch.setattr(dossier, "DOSSIER_DIR", tmp_path / "dossier")

    first = client.post("/api/dossier", json={"target": "alice", "results": [
        {"name": "get_followers", "result": [{"id": "1", "username": "anna"}]}]}).json()
    second = client.post("/api/dossier", json={"target": "alice", "results": [
        {"name": "get_followers", "result": [{"id": "2", "username": "bruno"}]}]}).json()
    assert first["id"] and second["id"]

    listed = client.get("/api/dossier", params={"target": "alice"}).json()
    assert len(listed) == 2

    reopened = client.get(f"/api/dossier/alice/{second['id']}").json()
    assert reopened["results"][0]["result"][0]["username"] == "bruno"

    diff = client.get(f"/api/dossier/alice/{first['id']}/diff/{second['id']}").json()
    entry = diff["commands"][0]
    assert entry["added"] == ["bruno"] and entry["removed"] == ["anna"]

    assert client.delete(f"/api/dossier/alice/{first['id']}").json() == {"deleted": True}
    assert len(client.get("/api/dossier", params={"target": "alice"}).json()) == 1


def test_dossier_requires_a_target(client):
    assert client.post("/api/dossier", json={"results": []}).status_code == 400


def test_dossier_missing_is_404(client, tmp_path, monkeypatch):
    from osint_ig.evidence import cases as dossier
    monkeypatch.setattr(dossier, "DOSSIER_DIR", tmp_path / "dossier")
    assert client.get("/api/dossier/alice/nope").status_code == 404


def test_cache_clear_endpoint(client):
    assert "cleared" in client.delete("/api/cache").json()


def test_about_endpoint(client):
    data = client.get("/api/about").json()
    assert data["product_name"] == "OSINT IG"
    assert data["author"] == "Mohsin Khawaja"
    assert data["organization"] == "CSIB"
    libs = {lib["name"] for lib in data["libraries"]}
    assert {"fastapi", "instagrapi", "google-genai"} <= libs
    assert "hikerapi" not in libs
    assert "ollama" not in libs


def test_security_headers(client):
    h = client.get("/api/tools").headers
    assert h["cache-control"] == "no-store"
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "no-referrer"


def test_user_info_cost_estimate(client):
    specs = {s["name"]: s for s in client.get("/api/tools").json()}
    assert "get_user_info" in specs
    assert "get_account_about" not in specs
    assert "get_suggested_profiles" not in specs

    from osint_ig.processing import estimator as cost
    assert cost.estimate_command("get_user_info", {}, {}) == (0, 0)
