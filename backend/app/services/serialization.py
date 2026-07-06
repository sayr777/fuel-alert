from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportPhoto
from app.models.user import User
from app.schemas.report import PhotoOut, ReportFeature, ReportProperties
from app.services import storage


async def report_to_feature(session: AsyncSession, report: Report) -> ReportFeature:
    point = to_shape(report.geom)
    nickname_result = await session.execute(select(User.nickname).where(User.id == report.user_id))
    nickname = nickname_result.scalar_one_or_none() or "Аноним"

    photos_result = await session.execute(select(ReportPhoto).where(ReportPhoto.report_id == report.id))
    photos = [PhotoOut(url=storage.public_url(p.s3_key), taken_at=p.exif_taken_at) for p in photos_result.scalars()]

    return ReportFeature(
        geometry={"type": "Point", "coordinates": [point.x, point.y]},
        properties=ReportProperties(
            id=report.id,
            event_type=report.event_type,
            fuel_grades=report.fuel_grades,
            description=report.description,
            price=float(report.price) if report.price is not None else None,
            extra=report.extra,
            event_at=report.event_at,
            nickname=nickname,
            station_id=report.station_id,
            photos=photos,
            confirmations_count=report.confirmations_count,
            review_flags=report.review_flags,
        ),
    )
