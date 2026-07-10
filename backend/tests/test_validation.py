"""Tests for the report validation pipeline.

DB session and Redis are mocked — no infrastructure required.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.services.validation import NewReportInput, ReportRejected, validate_and_create_report


def _payload(**overrides) -> NewReportInput:
    defaults = dict(
        user_id=1,
        telegram_id=12345,
        event_type="NO_FUEL",
        lon=37.62,
        lat=55.75,
        event_at=datetime.now(timezone.utc),
        fuel_grades=["AI95"],
    )
    defaults.update(overrides)
    return NewReportInput(**defaults)


def _session(dup=None, station=None) -> AsyncMock:
    """Mock AsyncSession with configurable find_duplicate / find_nearest_station results."""
    session = AsyncMock(spec=AsyncSession)

    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = dup

    station_result = MagicMock()
    station_result.scalar_one_or_none.return_value = station

    session.execute.side_effect = [dup_result, station_result]
    return session


_PASS_RATE_LIMIT = patch("app.services.validation.check_rate_limit", return_value=True)


# --- hard rejections ---

async def test_unknown_event_type_rejected():
    with pytest.raises(ReportRejected, match="unknown event_type"):
        await validate_and_create_report(AsyncMock(), _payload(event_type="DOES_NOT_EXIST"))


async def test_rate_limit_rejected():
    with patch("app.services.validation.check_rate_limit", return_value=False):
        with pytest.raises(ReportRejected, match="rate_limit_exceeded"):
            await validate_and_create_report(AsyncMock(), _payload())


async def test_outside_region_rejected():
    with _PASS_RATE_LIMIT:
        with pytest.raises(ReportRejected, match="outside_coverage_region"):
            await validate_and_create_report(AsyncMock(), _payload(lon=0.0, lat=51.5))


async def test_event_too_old_rejected():
    old = datetime.now(timezone.utc) - timedelta(hours=100)
    with _PASS_RATE_LIMIT:
        with pytest.raises(ReportRejected, match="event_too_old"):
            await validate_and_create_report(AsyncMock(), _payload(event_at=old))


async def test_event_in_future_rejected():
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    with _PASS_RATE_LIMIT:
        with pytest.raises(ReportRejected, match="event_at_in_future"):
            await validate_and_create_report(AsyncMock(), _payload(event_at=future))


# --- happy path ---

async def test_published_without_nearby_station():
    session = _session()
    with _PASS_RATE_LIMIT:
        report = await validate_and_create_report(session, _payload())

    assert report.event_type == "NO_FUEL"
    assert report.status == "published"
    assert report.station_id is None
    session.add.assert_called_once_with(report)


async def test_published_with_nearby_station():
    fake_station = MagicMock()
    fake_station.id = 7
    session = _session(station=fake_station)

    with _PASS_RATE_LIMIT:
        report = await validate_and_create_report(session, _payload())

    assert report.status == "published"
    assert report.station_id == 7


async def test_requires_moderation_stays_pending():
    session = _session()
    with _PASS_RATE_LIMIT:
        report = await validate_and_create_report(session, _payload(event_type="ILLEGAL_SALE"))

    assert report.status == "pending"


async def test_review_flags_send_to_pending():
    session = _session()
    payload = _payload(review_flags=["exif_gps_mismatch"])
    with _PASS_RATE_LIMIT:
        report = await validate_and_create_report(session, payload)

    assert report.status == "pending"
    assert report.review_flags == ["exif_gps_mismatch"]


# --- duplicate detection ---

async def test_duplicate_increments_confirmations():
    existing = MagicMock(spec=Report)
    existing.id = 42
    existing.confirmations_count = 3

    session = AsyncMock(spec=AsyncSession)
    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = existing
    session.execute.return_value = dup_result

    with _PASS_RATE_LIMIT:
        report = await validate_and_create_report(session, _payload())

    assert report.status == "duplicate"
    assert report.duplicate_of == 42
    assert existing.confirmations_count == 4
