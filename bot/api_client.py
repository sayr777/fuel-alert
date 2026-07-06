from datetime import datetime
from typing import Any

import aiohttp

from config import get_settings

settings = get_settings()


class ApiClient:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(base_url=settings.api_base_url)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def register_user(self, telegram_id: int, nickname: str | None = None) -> dict[str, Any]:
        session = await self._get_session()
        payload: dict[str, Any] = {"telegram_id": telegram_id}
        if nickname:
            payload["nickname"] = nickname
        async with session.post("/users/register", json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_event_types(self) -> list[dict[str, Any]]:
        session = await self._get_session()
        async with session.get("/event-types") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_fuel_grades(self) -> list[str]:
        session = await self._get_session()
        async with session.get("/fuel-grades") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def submit_report(
        self,
        *,
        telegram_id: int,
        event_type: str,
        lat: float,
        lon: float,
        event_at: datetime | None = None,
        fuel_grades: list[str] | None = None,
        description: str | None = None,
        price: float | None = None,
        extra: dict[str, Any] | None = None,
        photos: list[tuple[str, bytes]] | None = None,
    ) -> dict[str, Any]:
        session = await self._get_session()
        form = aiohttp.FormData()
        form.add_field("telegram_id", str(telegram_id))
        form.add_field("event_type", event_type)
        form.add_field("lat", str(lat))
        form.add_field("lon", str(lon))
        if event_at:
            form.add_field("event_at", event_at.isoformat())
        if fuel_grades:
            form.add_field("fuel_grades", ",".join(fuel_grades))
        if description:
            form.add_field("description", description)
        if price is not None:
            form.add_field("price", str(price))
        if extra:
            import json

            form.add_field("extra", json.dumps(extra, ensure_ascii=False))

        if photos:
            for filename, data in photos:
                form.add_field("photos", data, filename=filename, content_type="image/jpeg")

        async with session.post("/reports", data=form) as resp:
            resp.raise_for_status()
            return await resp.json()