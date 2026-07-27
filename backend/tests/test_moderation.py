"""Tests for new moderation endpoints: unpublish, restore, health.

Uses Authorization: Bearer header (as required by require_moderator dep).
Session is mocked per-test — no real DB needed.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_session
from app.deps import require_moderator
from app.main import app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
WRONG_AUTH = {"Authorization": "Bearer wrong"}


def _mk_session(report=None):
    """Return a mock AsyncSession generator. report is returned by scalar_one_or_none."""
    async def _session():
        mock = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = report
        result.scalars.return_value.all.return_value = []
        mock.execute.return_value = result
        mock.commit = AsyncMock()
        mock.add = MagicMock()
        yield mock
    return _session


@pytest.fixture(autouse=True)
def _mock_deps():
    """Override DB session and moderator auth for all tests in this file."""
    app.dependency_overrides[require_moderator] = lambda: TOKEN
    app.dependency_overrides[get_session] = _mk_session()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ── auth guard ──────────────────────────────────────────────────────────────

def test_queue_ok_empty(client):
    r = client.get("/api/v1/moderation/queue", headers=AUTH)
    assert r.status_code == 200
    assert r.json() == []


def test_published_ok_empty(client):
    r = client.get("/api/v1/moderation/published", headers=AUTH)
    assert r.status_code == 200
    assert r.json() == []


def test_rejected_ok_empty(client):
    r = client.get("/api/v1/moderation/rejected", headers=AUTH)
    assert r.status_code == 200
    assert r.json() == []


# ── publish / reject ────────────────────────────────────────────────────────

def test_publish_not_found(client):
    r = client.post("/api/v1/moderation/99/publish", headers=AUTH, data={"moderator_id": "mod"})
    assert r.status_code == 404


def test_publish_ok(client):
    mock_report = MagicMock()
    mock_report.id = 1
    mock_report.status = "pending"
    app.dependency_overrides[get_session] = _mk_session(report=mock_report)

    r = client.post("/api/v1/moderation/1/publish", headers=AUTH, data={"moderator_id": "mod"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "status": "published"}
    assert mock_report.status == "published"


def test_reject_not_found(client):
    r = client.post("/api/v1/moderation/99/reject", headers=AUTH, data={"moderator_id": "mod", "reason": "spam"})
    assert r.status_code == 404


def test_reject_ok(client):
    mock_report = MagicMock()
    mock_report.id = 2
    mock_report.status = "pending"
    app.dependency_overrides[get_session] = _mk_session(report=mock_report)

    r = client.post("/api/v1/moderation/2/reject", headers=AUTH, data={"moderator_id": "mod", "reason": "spam"})
    assert r.status_code == 200
    assert r.json() == {"id": 2, "status": "rejected"}
    assert mock_report.status == "rejected"
    assert mock_report.reject_reason == "spam"


# ── unpublish ────────────────────────────────────────────────────────────────

def test_unpublish_not_found(client):
    r = client.post("/api/v1/moderation/5/unpublish", headers=AUTH, data={"moderator_id": "mod", "reason": "removed"})
    assert r.status_code == 404


def test_unpublish_ok(client):
    mock_report = MagicMock()
    mock_report.id = 5
    mock_report.status = "published"
    app.dependency_overrides[get_session] = _mk_session(report=mock_report)

    r = client.post("/api/v1/moderation/5/unpublish", headers=AUTH, data={"moderator_id": "mod", "reason": "spam"})
    assert r.status_code == 200
    assert r.json() == {"id": 5, "status": "rejected"}
    assert mock_report.status == "rejected"
    assert mock_report.reject_reason == "spam"


# ── restore ──────────────────────────────────────────────────────────────────

def test_restore_not_found(client):
    r = client.post("/api/v1/moderation/7/restore", headers=AUTH, data={"moderator_id": "mod"})
    assert r.status_code == 404


def test_restore_ok(client):
    mock_report = MagicMock()
    mock_report.id = 7
    mock_report.status = "rejected"
    mock_report.reject_reason = "spam"
    app.dependency_overrides[get_session] = _mk_session(report=mock_report)

    r = client.post("/api/v1/moderation/7/restore", headers=AUTH, data={"moderator_id": "mod"})
    assert r.status_code == 200
    assert r.json() == {"id": 7, "status": "published"}
    assert mock_report.status == "published"
    assert mock_report.reject_reason is None


# ── health ───────────────────────────────────────────────────────────────────

def test_health_structure(client):
    with (
        patch("app.routers.moderation._check_redis", return_value={"status": "ok", "latency_ms": 1}),
        patch("app.routers.moderation._check_telegram", return_value={"status": "ok", "latency_ms": 50}),
        patch("app.routers.moderation._check_docker", return_value=[{"name": "api", "status": "Up", "running": True}]),
    ):
        r = client.get("/api/v1/moderation/health", headers=AUTH)

    assert r.status_code == 200
    body = r.json()
    assert "timestamp" in body
    assert body["database"]["status"] == "ok"
    assert body["redis"]["status"] == "ok"
    assert body["telegram"]["status"] == "ok"
    assert isinstance(body["containers"], list)


def test_health_redis_error_still_200(client):
    with (
        patch("app.routers.moderation._check_redis", return_value={"status": "error", "detail": "timeout"}),
        patch("app.routers.moderation._check_telegram", return_value={"status": "ok", "latency_ms": 50}),
        patch("app.routers.moderation._check_docker", return_value=[]),
    ):
        r = client.get("/api/v1/moderation/health", headers=AUTH)

    assert r.status_code == 200
    assert r.json()["redis"]["status"] == "error"
