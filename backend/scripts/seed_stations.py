"""Import fuel stations from OpenStreetMap (Overpass API) into the stations table."""

import asyncio
import json
import urllib.request

from sqlalchemy import func, select

from app.config import get_settings
from app.database import async_session_maker
from app.models.station import Station

settings = get_settings()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _build_query() -> str:
    min_lon, min_lat, max_lon, max_lat = settings.region_bbox
    return f"""
[out:json][timeout:90];
(
  node["amenity"="fuel"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["amenity"="fuel"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out center;
"""


def _fetch_osm() -> list[dict]:
    query = _build_query()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=f"data={urllib.request.quote(query)}".encode(),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data.get("elements", [])


def _parse_element(el: dict) -> tuple[str, str | None, str | None, float, float] | None:
    tags = el.get("tags", {})
    name = tags.get("name") or tags.get("brand") or tags.get("operator") or "АЗС"
    brand = tags.get("brand") or tags.get("operator")
    address = tags.get("addr:full") or tags.get("addr:street")

    if el["type"] == "node":
        lat, lon = el.get("lat"), el.get("lon")
    else:
        center = el.get("center") or {}
        lat, lon = center.get("lat"), center.get("lon")

    if lat is None or lon is None:
        return None
    return name, brand, address, float(lat), float(lon)


async def seed() -> None:
    async with async_session_maker() as session:
        count_result = await session.execute(select(func.count()).select_from(Station))
        existing = count_result.scalar_one()
        if existing:
            print(f"Stations table already has {existing} rows — skipping.")
            return

    try:
        elements = await asyncio.to_thread(_fetch_osm)
    except Exception as exc:
        print(f"OSM import skipped ({exc}). Stations can be seeded later.")
        return

    parsed = [p for el in elements if (p := _parse_element(el)) is not None]

    if not parsed:
        print("No stations returned from Overpass.")
        return

    async with async_session_maker() as session:
        for name, brand, address, lat, lon in parsed:
            session.add(
                Station(
                    name=name[:255],
                    brand=brand[:128] if brand else None,
                    address=address[:255] if address else None,
                    geom=f"SRID=4326;POINT({lon} {lat})",
                )
            )
        await session.commit()

    print(f"Imported {len(parsed)} stations from OSM.")


if __name__ == "__main__":
    asyncio.run(seed())