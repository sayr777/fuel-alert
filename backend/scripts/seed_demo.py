"""Seed demo users and published reports for local map testing."""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database import async_session_maker
from app.models.report import Report
from app.models.user import User

DEMO_REPORTS = [
    {
        "event_type": "NO_FUEL",
        "fuel_grades": ["AI95", "DT"],
        "description": "На всех колонках табличка «топливо закончилось»",
        "lat": 53.045,
        "lon": 158.628,
        "hours_ago": 2,
    },
    {
        "event_type": "FUEL_AVAILABLE",
        "fuel_grades": ["AI92", "AI95"],
        "price": 68.9,
        "description": "Топливо появилось, очередь небольшая",
        "lat": 53.018,
        "lon": 158.655,
        "hours_ago": 1,
    },
    {
        "event_type": "LONG_QUEUE",
        "extra": {"wait_minutes": 45},
        "description": "Очередь до въезда на территорию",
        "lat": 53.062,
        "lon": 158.595,
        "hours_ago": 0.5,
    },
    {
        "event_type": "LIMITED_SALE",
        "fuel_grades": ["DT"],
        "extra": {"limit_liters": 40},
        "description": "Дизель — не более 40 л в одни руки",
        "lat": 52.987,
        "lon": 158.702,
        "hours_ago": 3,
    },
    {
        "event_type": "OVERPRICE",
        "fuel_grades": ["AI95"],
        "price": 89.5,
        "description": "Цена заметно выше соседних АЗС",
        "lat": 53.091,
        "lon": 158.581,
        "hours_ago": 5,
    },
    {
        "event_type": "ILLEGAL_SALE",
        "description": "Продажа канистрами у обочины, без лицензии",
        "lat": 53.035,
        "lon": 158.640,
        "hours_ago": 0.25,
        "status": "pending",
    },
]


async def seed() -> None:
    async with async_session_maker() as session:
        report_count = await session.execute(select(func.count()).select_from(Report))
        if report_count.scalar_one():
            print("Reports already exist — skipping demo seed.")
            return

        user_result = await session.execute(select(User).where(User.telegram_id == 900000001))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=900000001, nickname="Демо-Водитель")
            session.add(user)
            await session.flush()

        now = datetime.now(timezone.utc)
        for item in DEMO_REPORTS:
            event_at = now - timedelta(hours=item["hours_ago"])
            session.add(
                Report(
                    user_id=user.id,
                    event_type=item["event_type"],
                    fuel_grades=item.get("fuel_grades"),
                    description=item.get("description"),
                    price=item.get("price"),
                    extra=item.get("extra"),
                    event_at=event_at,
                    geom=f"SRID=4326;POINT({item['lon']} {item['lat']})",
                    status=item.get("status", "published"),
                    confirmations_count=0 if item.get("status") == "pending" else 1,
                )
            )

        await session.commit()
    print(f"Seeded {len(DEMO_REPORTS)} demo reports.")


if __name__ == "__main__":
    asyncio.run(seed())