import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.station import Station

settings = get_settings()


def point_in_region(lon: float, lat: float) -> bool:
    """Bbox check against the configured region coverage.

    A real deployment should swap this for a proper polygon (ST_Contains against
    a stored region boundary) — the bbox is a placeholder that also lets through
    points on the fringe of neighbouring regions that share the same box.
    """
    min_lon, min_lat, max_lon, max_lat = settings.region_bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


async def find_nearest_station(session: AsyncSession, lon: float, lat: float, radius_m: float) -> Station | None:
    point = f"SRID=4326;POINT({lon} {lat})"
    stmt = (
        select(Station)
        .where(Station.geom.ST_DWithin(point, radius_m, use_spheroid=True))
        .order_by(Station.geom.ST_Distance(point))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
