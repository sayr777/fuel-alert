"""Create database tables and enable PostGIS. Run once after docker-compose up."""

import asyncio

from sqlalchemy import text

from app.database import Base, engine
from app.models import ModerationLog, Report, ReportPhoto, Station, User  # noqa: F401


async def init() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(init())