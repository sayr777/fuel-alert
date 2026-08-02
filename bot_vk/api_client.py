import aiohttp
from datetime import datetime


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_event_types(self) -> list[dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.base_url}/event_types") as r:
                return await r.json()

    async def get_fuel_grades(self) -> list[str]:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.base_url}/fuel_grades") as r:
                return await r.json()

    async def register_user(self, vk_id: int, username: str) -> None:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{self.base_url}/users/register", data={
                "telegram_id": vk_id,
                "username": username,
            })

    async def submit_report(
        self,
        vk_id: int,
        event_type: str,
        lat: float,
        lon: float,
        event_at: datetime,
        fuel_grades: list[str] | None = None,
        description: str | None = None,
        photos: list[tuple[str, bytes]] | None = None,
    ) -> dict:
        data = aiohttp.FormData()
        data.add_field("telegram_id", str(vk_id))
        data.add_field("event_type", event_type)
        data.add_field("lat", str(lat))
        data.add_field("lon", str(lon))
        data.add_field("event_at", event_at.isoformat())
        if fuel_grades:
            data.add_field("fuel_grades", ",".join(fuel_grades))
        if description:
            data.add_field("description", description)
        if photos:
            for filename, blob in photos:
                data.add_field("photos", blob, filename=filename, content_type="image/jpeg")
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.base_url}/reports", data=data) as r:
                return await r.json()
