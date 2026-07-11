import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models.report import Report, ReportPhoto
from app.models.user import User
from app.schemas.report import ReportFeature, ReportFeatureCollection, ReportSubmitResult
from app.services.exif import extract_exif
from app.services.serialization import report_to_feature
from app.services import storage
from app.services.validation import NewReportInput, ReportRejected, check_exif_consistency, validate_and_create_report

router = APIRouter(tags=["reports"])
settings = get_settings()


@router.post("/reports", response_model=ReportSubmitResult)
async def submit_report(
    telegram_id: int = Form(...),
    event_type: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    event_at: datetime | None = Form(None),
    fuel_grades: str | None = Form(None, description="Comma-separated grade codes"),
    description: str | None = Form(None),
    price: float | None = Form(None),
    extra: str | None = Form(None, description="JSON object of type-specific attributes"),
    source_msg_id: int | None = Form(None),
    photos: list[UploadFile] = File(default=[]),
    session: AsyncSession = Depends(get_session),
) -> ReportSubmitResult:
    if len(photos) > settings.max_photos_per_report:
        raise HTTPException(400, detail=f"max {settings.max_photos_per_report} photos per report")
    if description and len(description) > settings.max_description_length:
        raise HTTPException(400, detail=f"description exceeds {settings.max_description_length} chars")

    user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="user not registered — call /users/register first")
    if user.is_banned:
        raise HTTPException(403, detail="user is banned")

    grades = [g.strip() for g in fuel_grades.split(",") if g.strip()] if fuel_grades else None
    extra_data: dict | None = None
    if extra:
        if len(extra) > 4096:
            raise HTTPException(400, detail="extra field too large")
        parsed = json.loads(extra)
        if not isinstance(parsed, dict):
            raise HTTPException(400, detail="extra must be a JSON object")
        extra_data = parsed
    event_dt = event_at or datetime.now(timezone.utc)
    if event_dt.tzinfo is None:
        event_dt = event_dt.replace(tzinfo=timezone.utc)

    photo_blobs = [await p.read() for p in photos]
    photo_exif = [extract_exif(blob) for blob in photo_blobs]
    review_flags: list[str] = []
    for taken_at, gps in photo_exif:
        review_flags.extend(check_exif_consistency(taken_at, gps, event_dt, lon, lat))
    review_flags = sorted(set(review_flags))

    payload = NewReportInput(
        user_id=user.id,
        telegram_id=telegram_id,
        event_type=event_type,
        lon=lon,
        lat=lat,
        event_at=event_dt,
        fuel_grades=grades,
        description=description,
        price=price,
        extra=extra_data,
        source_msg_id=source_msg_id,
        review_flags=review_flags,
    )

    try:
        report = await validate_and_create_report(session, payload)
    except ReportRejected as exc:
        await session.rollback()
        return ReportSubmitResult(id=0, status="rejected", reject_reason=exc.reason)

    for blob, (taken_at, gps) in zip(photo_blobs, photo_exif):
        s3_key = storage.upload_photo(blob)
        photo = ReportPhoto(
            report_id=report.id,
            s3_key=s3_key,
            sha256=storage.sha256_bytes(blob),
            exif_taken_at=taken_at,
            exif_gps=f"SRID=4326;POINT({gps[0]} {gps[1]})" if gps else None,
        )
        session.add(photo)

    await session.commit()

    return ReportSubmitResult(
        id=report.id,
        status=report.status,
        duplicate_of=report.duplicate_of,
        confirmations_count=report.confirmations_count,
    )


@router.post("/reports/{report_id}/confirm", response_model=ReportSubmitResult)
async def confirm_report(report_id: int, telegram_id: int = Form(...), session: AsyncSession = Depends(get_session)) -> ReportSubmitResult:
    user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="user not registered")
    if user.is_banned:
        raise HTTPException(403, detail="user is banned")

    report_result = await session.execute(select(Report).where(Report.id == report_id, Report.status == "published"))
    report = report_result.scalar_one_or_none()
    if report is None:
        raise HTTPException(404, detail="report not found")
    if report.user_id == user.id:
        raise HTTPException(400, detail="cannot confirm your own report")

    report.confirmations_count += 1
    await session.commit()
    return ReportSubmitResult(id=report.id, status=report.status, confirmations_count=report.confirmations_count)


@router.get("/reports", response_model=ReportFeatureCollection)
async def list_reports(
    types: str | None = Query(None, description="Comma-separated event type codes"),
    grades: str | None = Query(None, description="Comma-separated fuel grade codes"),
    date_from: datetime | None = Query(None, alias="from"),
    date_to: datetime | None = Query(None, alias="to"),
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    status: str = Query("published"),
    limit: int = Query(200, le=500),
    session: AsyncSession = Depends(get_session),
) -> ReportFeatureCollection:
    if status != "published":
        # Non-public statuses are only for the moderation queue (see routers/moderation.py),
        # which uses its own auth — the public endpoint never leaks pending/rejected reports.
        raise HTTPException(400, detail="only status=published is available on this endpoint")

    stmt = select(Report).where(Report.status == "published")

    if types:
        stmt = stmt.where(Report.event_type.in_(types.split(",")))
    if grades:
        grade_list = grades.split(",")
        stmt = stmt.where(Report.fuel_grades.overlap(grade_list))
    if date_from:
        stmt = stmt.where(Report.event_at >= date_from)
    if date_to:
        stmt = stmt.where(Report.event_at <= date_to)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox.split(","))
        envelope = f"SRID=4326;POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"
        stmt = stmt.where(Report.geom.ST_Intersects(envelope))

    stmt = stmt.order_by(Report.event_at.desc()).limit(limit)

    result = await session.execute(stmt)
    reports = result.scalars().all()
    features = [await report_to_feature(session, r) for r in reports]
    return ReportFeatureCollection(features=features)


@router.get("/reports/{report_id}", response_model=ReportFeature)
async def get_report(report_id: int, session: AsyncSession = Depends(get_session)) -> ReportFeature:
    result = await session.execute(select(Report).where(Report.id == report_id, Report.status == "published"))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(404, detail="report not found")
    return await report_to_feature(session, report)
