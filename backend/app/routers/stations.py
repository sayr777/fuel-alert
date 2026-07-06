from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.station import Station
from app.schemas.station import StationOut

router = APIRouter(tags=["stations"])


@router.get("/stations", response_model=list[StationOut])
async def list_stations(
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    session: AsyncSession = Depends(get_session),
) -> list[StationOut]:
    stmt = select(Station)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox.split(","))
        envelope = f"SRID=4326;POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"
        stmt = stmt.where(Station.geom.ST_Intersects(envelope))

    result = await session.execute(stmt)
    stations = result.scalars().all()

    out = []
    for s in stations:
        point = to_shape(s.geom)
        out.append(StationOut(id=s.id, name=s.name, brand=s.brand, address=s.address, lat=point.y, lon=point.x))
    return out
