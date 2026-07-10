"""API-level tests.

Overrides the DB session dependency so no real database is required.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.main import app


@pytest.fixture(autouse=True)
def _mock_db():
    async def _session():
        mock = AsyncMock(spec=AsyncSession)
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        result.scalar_one.return_value = 0
        mock.execute.return_value = result
        yield mock

    app.dependency_overrides[get_session] = _session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- static endpoints (no DB) ---

def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_event_types_all_present(client):
    resp = client.get("/api/v1/event-types")
    assert resp.status_code == 200
    codes = {et["code"] for et in resp.json()}
    assert codes == {
        "NO_FUEL", "FUEL_AVAILABLE", "LIMITED_SALE", "LONG_QUEUE",
        "OVERPRICE", "ILLEGAL_SALE", "SHORT_MEASURE", "FAKE_FUEL",
        "STATION_CLOSED", "FRAUD",
    }


def test_event_types_schema(client):
    resp = client.get("/api/v1/event-types")
    et = next(e for e in resp.json() if e["code"] == "NO_FUEL")
    assert et["requires_moderation"] is False
    assert et["ttl_hours"] == 24
    assert "fuel_grades" in et["attributes"]


def test_fuel_grades(client):
    grades = client.get("/api/v1/fuel-grades").json()
    for grade in ("AI92", "AI95", "AI98", "DT", "GAS"):
        assert grade in grades


# --- reports ---

def test_list_reports_empty(client):
    resp = client.get("/api/v1/reports")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert body["features"] == []


def test_list_reports_rejects_non_published_status(client):
    resp = client.get("/api/v1/reports?status=pending")
    assert resp.status_code == 400


def test_get_report_not_found(client):
    resp = client.get("/api/v1/reports/999")
    assert resp.status_code == 404


# --- moderation auth ---

def test_moderation_queue_missing_token(client):
    # X-Moderator-Token is a required Header → FastAPI returns 422
    resp = client.get("/api/v1/moderation/queue")
    assert resp.status_code == 422


def test_moderation_queue_wrong_token(client):
    resp = client.get("/api/v1/moderation/queue", headers={"X-Moderator-Token": "wrong-token"})
    assert resp.status_code == 401


def test_moderation_publish_wrong_token(client):
    resp = client.post(
        "/api/v1/moderation/1/publish",
        headers={"X-Moderator-Token": "wrong"},
        data={"moderator_id": "mod1"},
    )
    assert resp.status_code == 401
