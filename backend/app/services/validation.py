from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.event_types import get_event_type
from app.models.report import Report
from app.services.geo import find_nearest_station, haversine_m, point_in_region
from app.services.rate_limit import check_rate_limit

settings = get_settings()


class ReportRejected(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class NewReportInput:
    user_id: int
    telegram_id: int
    event_type: str
    lon: float
    lat: float
    event_at: datetime
    fuel_grades: list[str] | None = None
    description: str | None = None
    price: float | None = None
    extra: dict | None = None
    source_msg_id: int | None = None
    review_flags: list[str] = field(default_factory=list)


async def find_duplicate(session: AsyncSession, payload: NewReportInput) -> Report | None:
    """Same user + same event type within dedup_radius_m and dedup_window_minutes."""
    window_start = payload.event_at - timedelta(minutes=settings.dedup_window_minutes)
    point = f"SRID=4326;POINT({payload.lon} {payload.lat})"

    stmt = (
        select(Report)
        .where(
            Report.user_id == payload.user_id,
            Report.event_type == payload.event_type,
            Report.event_at >= window_start,
            Report.status != "rejected",
            Report.duplicate_of.is_(None),
            Report.geom.ST_DWithin(point, settings.dedup_radius_m, use_spheroid=True),
        )
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def validate_and_create_report(session: AsyncSession, payload: NewReportInput) -> Report:
    """Runs the automatic validation pipeline and persists the resulting report.

    Raises ReportRejected for hard failures (rate limit, out of region, stale event_at).
    Soft issues (EXIF mismatches etc.) go into review_flags instead of blocking ingestion —
    see docs/moderation.md for how those reach the moderator queue.
    """
    event_type = get_event_type(payload.event_type)
    if event_type is None:
        raise ReportRejected(f"unknown event_type: {payload.event_type}")

    if not await check_rate_limit(payload.telegram_id):
        raise ReportRejected("rate_limit_exceeded")

    if not point_in_region(payload.lon, payload.lat):
        raise ReportRejected("outside_coverage_region")

    now = datetime.now(timezone.utc)
    if payload.event_at > now + timedelta(minutes=5):
        raise ReportRejected("event_at_in_future")
    if now - payload.event_at > timedelta(hours=settings.max_event_age_hours):
        raise ReportRejected("event_too_old")

    duplicate = await find_duplicate(session, payload)
    if duplicate is not None:
        report = Report(
            user_id=payload.user_id,
            event_type=payload.event_type,
            fuel_grades=payload.fuel_grades,
            description=payload.description,
            price=payload.price,
            extra=payload.extra,
            event_at=payload.event_at,
            geom=f"SRID=4326;POINT({payload.lon} {payload.lat})",
            status="duplicate",
            duplicate_of=duplicate.id,
            source_msg_id=payload.source_msg_id,
            review_flags=payload.review_flags or None,
        )
        duplicate.confirmations_count += 1
        session.add(report)
        await session.flush()
        return report

    station = await find_nearest_station(session, payload.lon, payload.lat, settings.station_match_radius_m)

    status = "pending" if (event_type.requires_moderation or payload.review_flags) else "published"

    report = Report(
        user_id=payload.user_id,
        event_type=payload.event_type,
        fuel_grades=payload.fuel_grades,
        description=payload.description,
        price=payload.price,
        extra=payload.extra,
        event_at=payload.event_at,
        geom=f"SRID=4326;POINT({payload.lon} {payload.lat})",
        station_id=station.id if station else None,
        status=status,
        source_msg_id=payload.source_msg_id,
        review_flags=payload.review_flags or None,
    )
    session.add(report)
    await session.flush()
    return report


def check_exif_consistency(
    exif_taken_at: datetime | None,
    exif_lon_lat: tuple[float, float] | None,
    event_at: datetime,
    report_lon: float,
    report_lat: float,
) -> list[str]:
    """Returns review_flags raised by a photo's EXIF metadata, if any."""
    flags: list[str] = []

    if exif_taken_at is not None:
        taken_at = exif_taken_at if exif_taken_at.tzinfo else exif_taken_at.replace(tzinfo=timezone.utc)
        if abs((taken_at - event_at).total_seconds()) > 3600 * 3:
            flags.append("exif_time_mismatch")

    if exif_lon_lat is not None:
        exif_lon, exif_lat = exif_lon_lat
        distance_km = haversine_m(exif_lon, exif_lat, report_lon, report_lat) / 1000
        if distance_km > settings.exif_gps_mismatch_km:
            flags.append("exif_gps_mismatch")

    return flags
