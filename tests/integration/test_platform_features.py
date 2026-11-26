"""Tests for OSINT IG specific endpoints: Dashboard, Instagram settings,
optional Gemini AI integration, report exports, and HikerAPI/Ollama removal."""
import types

import pytest
from fastapi.testclient import TestClient

import osint_ig.api.app as appmod
import osint_ig.evidence.cases as dossier
import osint_ig.ai.gemini_analyzer as gemini_svc
import osint_ig.database.history_store as history


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(gemini_svc, "GEMINI_CONFIG_PATH", tmp_path / "gemini.json")
    monkeypatch.setattr(dossier, "DOSSIER_DIR", tmp_path / "dossier")
    history.targets.path = tmp_path / "targets.json"
    history.queries.path = tmp_path / "queries.json"

    monkeypatch.setattr(
        appmod,
        "get_session_status",
        lambda: {
            "backend": "instagrapi",
            "session_exists": True,
            "connected": True,
            "username": "test_session",
            "user_id": "12345",
            "credentials_configured": True,
        },
    )
    return TestClient(appmod.app, base_url="http://127.0.0.1:8000")


def test_hikerapi_and_ollama_endpoints_removed(client):
    assert client.get("/api/token").status_code == 404
    assert client.get("/api/balance").status_code == 404
    assert client.post("/api/query", json={"message": "hi"}).status_code in (404, 405)


def test_dashboard_returns_real_stats(client):
    client.post("/api/dossier", json={"target": "alice", "results": [{"name": "get_user_info", "result": {}}]})
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["total_investigations"] == 1
    assert body["stats"]["saved_reports"] == 1
    assert body["instagram_status"]["connected"] is True
    assert body["ai_status"]["configured"] is False


def test_instagram_settings_endpoints(client, monkeypatch):
    r = client.get("/api/settings/instagram")
    assert r.status_code == 200
    assert r.json()["backend"] == "instagrapi"

    monkeypatch.setattr(appmod, "save_session_by_sessionid", lambda sid: {"connected": True, "username": "ddose.clips", "user_id": "999"})
    r2 = client.post("/api/settings/instagram/session", json={"sessionid": "abc:123"})
    assert r2.status_code == 200
    assert r2.json()["username"] == "ddose.clips"

    monkeypatch.setattr(appmod, "verify_session", lambda: {"connected": True, "username": "ddose.clips", "user_id": "999"})
    r3 = client.post("/api/settings/instagram/verify")
    assert r3.status_code == 200
    assert r3.json()["connected"] is True

    monkeypatch.setattr(appmod, "login_with_credentials", lambda u, p: {"connected": True, "username": u, "user_id": "999"})
    r4 = client.post("/api/settings/instagram/credentials", json={"username": "ddose.clips", "password": "secret"})
    assert r4.status_code == 200
    assert r4.json()["username"] == "ddose.clips"

    # Localhost-only guard
    assert client.post("/api/settings/instagram/session", json={"sessionid": "x"}, headers={"host": "evil.example"}).status_code == 403
    assert client.post("/api/settings/instagram/credentials", json={"username": "a", "password": "b"}, headers={"host": "evil.example"}).status_code == 403


def test_gemini_optional_and_never_exposes_key(client):
    state = client.get("/api/ai/config").json()
    assert state["configured"] is False
    assert state["enabled"] is False

    # App still works without Gemini; analyze returns 400 with clear message
    r_err = client.post("/api/ai/analyze", json={"target": "alice", "results": []})
    assert r_err.status_code == 400
    assert "not configured" in r_err.json()["detail"].lower()

    saved = client.post("/api/ai/config", json={"api_key": "AIza_fake_secret_key_9876", "model": "gemini-4-hydrogen", "enabled": True})
    assert saved.status_code == 200
    body = saved.json()
    assert body["configured"] is True
    assert body["enabled"] is True
    assert body["preview"] == "AIza…9876"
    assert "AIza_fake_secret_key_9876" not in str(body)
    assert "AIza_fake_secret_key_9876" not in str(client.get("/api/ai/config").json())


def test_gemini_verify_and_analyze_with_synthetic_fixture(client, monkeypatch):
    calls = []

    class FakeInteractions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(output_text="### Observed Facts\n- [get_user_info] 120 followers.")

    monkeypatch.setattr(gemini_svc, "_make_client", lambda key: types.SimpleNamespace(interactions=FakeInteractions()))
    client.post("/api/ai/config", json={"api_key": "AIza_fake_secret_key_9876", "model": "gemini-4-hydrogen", "enabled": True})

    ver = client.post("/api/ai/verify", json={})
    assert ver.status_code == 200
    assert ver.json()["ok"] is True

    res = client.post("/api/ai/analyze", json={
        "target": "alice",
        "analysis_type": "profile_summary",
        "results": [{"name": "get_user_info", "is_error": False, "result": {"username": "alice", "follower_count": 120}}],
    })
    assert res.status_code == 200
    data = res.json()
    assert "Observed Facts" in data["analysis"]
    assert calls[-1]["store"] is False


def test_report_exports_all_formats(client, monkeypatch):
    import osint_ig.evidence.exporter as reports_mod

    class FakeResp:
        content = b"fake-jpeg-bytes"
        def raise_for_status(self):
            pass

    class FakeHttpClient:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def get(self, url):
            return FakeResp()

    monkeypatch.setattr(reports_mod.httpx, "Client", FakeHttpClient)

    run = {
        "id": "1700000000-abc123",
        "target": "alice",
        "backend": "instagrapi",
        "saved_at": 1700000000,
        "api_calls_total": 2,
        "results": [
            {"name": "get_user_info", "is_error": False, "elapsed_ms": 42, "result": {
                "username": "alice", "follower_count": 120,
                "public_email": "alice@example.com", "contact_phone_number": "+123456789",
            }},
            {"name": "get_followers", "is_error": False, "elapsed_ms": 10, "result": [
                {"id": "1", "username": "bob", "full_name": "Bob"},
            ]},
            {"name": "get_user_photos", "is_error": False, "elapsed_ms": 15, "result": [
                {"id": "p1", "url": "https://scontent.cdninstagram.com/v/p1.jpg"},
            ]},
        ],
    }

    r_html = client.post("/api/report/export", json={"run": run, "format": "html"})
    assert r_html.status_code == 200
    assert "OSINT IG" in r_html.text
    assert "Mohsin Khawaja" in r_html.text
    assert "CSIB" in r_html.text

    r_csv = client.post("/api/report/export", json={"run": run, "format": "csv"})
    assert r_csv.status_code == 200
    assert "get_user_info" in r_csv.text

    r_json = client.post("/api/report/export", json={"run": run, "format": "json"})
    assert r_json.status_code == 200
    assert r_json.json()["prepared_by"] == "Mohsin Khawaja"

    import io
    import zipfile
    r_zip = client.post("/api/report/export", json={"run": run, "format": "zip"})
    assert r_zip.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_zip.content)) as zf:
        names = set(zf.namelist())
        assert {
            "report.html",
            "report.json",
            "report.csv",
            "manifest.json",
            "raw_evidence/01_get_user_info.json",
            "lists/emails.csv",
            "lists/emails.txt",
            "lists/phone_numbers.csv",
            "lists/phone_numbers.txt",
            "lists/followers.csv",
            "lists/followers.txt",
            "media/001_p1.jpg",
        } <= names
