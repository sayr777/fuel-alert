from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import require_moderator
from app.models.moderation import ModerationLog
from app.models.report import Report
from app.schemas.report import ReportFeature
from app.services.serialization import report_to_feature

router = APIRouter(prefix="/moderation", tags=["moderation"], dependencies=[Depends(require_moderator)])


@router.get("/queue", response_model=list[ReportFeature])
async def moderation_queue(session: AsyncSession = Depends(get_session)) -> list[ReportFeature]:
    """Reports awaiting a human decision: status=pending covers both
    requires_moderation event types and anything the auto-pipeline flagged."""
    stmt = select(Report).where(Report.status == "pending").order_by(Report.created_at.asc())
    result = await session.execute(stmt)
    reports = result.scalars().all()
    return [await report_to_feature(session, r) for r in reports]


@router.get("/published", response_model=list[ReportFeature])
async def moderation_published(session: AsyncSession = Depends(get_session)) -> list[ReportFeature]:
    stmt = select(Report).where(Report.status == "published").order_by(Report.created_at.desc()).limit(500)
    result = await session.execute(stmt)
    reports = result.scalars().all()
    return [await report_to_feature(session, r) for r in reports]


@router.get("/rejected", response_model=list[ReportFeature])
async def moderation_rejected(session: AsyncSession = Depends(get_session)) -> list[ReportFeature]:
    stmt = select(Report).where(Report.status == "rejected").order_by(Report.created_at.desc()).limit(500)
    result = await session.execute(stmt)
    reports = result.scalars().all()
    return [await report_to_feature(session, r) for r in reports]


@router.post("/{report_id}/publish")
async def publish_report(
    report_id: int,
    moderator_id: str = Form(...),
    comment: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    report = await _get_pending_report(session, report_id)
    report.status = "published"
    session.add(ModerationLog(report_id=report_id, moderator_id=moderator_id, action="publish", comment=comment))
    await session.commit()
    return {"id": report_id, "status": "published"}


@router.post("/{report_id}/reject")
async def reject_report(
    report_id: int,
    moderator_id: str = Form(...),
    reason: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    report = await _get_pending_report(session, report_id)
    report.status = "rejected"
    report.reject_reason = reason
    session.add(ModerationLog(report_id=report_id, moderator_id=moderator_id, action="reject", comment=reason))
    await session.commit()
    return {"id": report_id, "status": "rejected"}


@router.post("/{report_id}/unpublish")
async def unpublish_report(
    report_id: int,
    moderator_id: str = Form(...),
    reason: str = Form("moderator_removed"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    report = await _get_report_by_status(session, report_id, "published")
    report.status = "rejected"
    report.reject_reason = reason
    session.add(ModerationLog(report_id=report_id, moderator_id=moderator_id, action="unpublish", comment=reason))
    await session.commit()
    return {"id": report_id, "status": "rejected"}


@router.post("/{report_id}/restore")
async def restore_report(
    report_id: int,
    moderator_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    report = await _get_report_by_status(session, report_id, "rejected")
    report.status = "published"
    report.reject_reason = None
    session.add(ModerationLog(report_id=report_id, moderator_id=moderator_id, action="restore", comment=None))
    await session.commit()
    return {"id": report_id, "status": "published"}


async def _get_pending_report(session: AsyncSession, report_id: int) -> Report:
    result = await session.execute(select(Report).where(Report.id == report_id, Report.status == "pending"))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(404, detail="pending report not found")
    return report


async def _get_report_by_status(session: AsyncSession, report_id: int, status: str) -> Report:
    result = await session.execute(select(Report).where(Report.id == report_id, Report.status == status))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(404, detail=f"report with status={status} not found")
    return report
