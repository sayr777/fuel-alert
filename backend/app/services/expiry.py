import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.database import async_session_maker
from app.event_types import EVENT_TYPES
from app.models.report import Report

logger = logging.getLogger(__name__)

_CHECK_INTERVAL_SECONDS = 300


async def expire_published_reports() -> int:
    """Flips published reports past their event type's TTL to status=expired.

    TTL is measured from event_at (when the situation happened), not created_at —
    a report submitted late about an old queue shouldn't outlive a fresh one.
    """
    now = datetime.now(timezone.utc)
    total = 0
    async with async_session_maker() as session:
        for code, event_type in EVENT_TYPES.items():
            cutoff = now - timedelta(hours=event_type.ttl_hours)
            stmt = (
                update(Report)
                .where(Report.event_type == code, Report.status == "published", Report.event_at < cutoff)
                .values(status="expired")
            )
            result = await session.execute(stmt)
            total += result.rowcount or 0
        await session.commit()
    return total


async def run_expiry_loop() -> None:
    while True:
        try:
            expired = await expire_published_reports()
            if expired:
                logger.info("Expired %d report(s)", expired)
        except Exception:
            logger.exception("Report expiry pass failed")
        await asyncio.sleep(_CHECK_INTERVAL_SECONDS)
