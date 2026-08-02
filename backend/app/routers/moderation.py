import asyncio
import http.client
import json
import socket
import time
import urllib.request
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.deps import require_moderator
from app.models.moderation import ModerationLog
from app.models.report import Report
from app.schemas.report import ReportFeature
from app.services.serialization import report_to_feature

router = APIRouter(prefix="/moderation", tags=["moderation"], dependencies=[Depends(require_moderator)])

DOCKER_SOCKET = "/var/run/docker.sock"


@router.get("/queue", response_model=list[ReportFeature])
async def moderation_queue(session: AsyncSession = Depends(get_session)) -> list[ReportFeature]:
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


@router.get("/expired", response_model=list[ReportFeature])
async def moderation_expired(session: AsyncSession = Depends(get_session)) -> list[ReportFeature]:
    stmt = select(Report).where(Report.status == "expired").order_by(Report.created_at.desc()).limit(500)
    result = await session.execute(stmt)
    reports = result.scalars().all()
    return [await report_to_feature(session, r) for r in reports]


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict:
    db_res, redis_res, tg_res, docker_res, sys_res = await asyncio.gather(
        _check_db(session),
        _check_redis(),
        _check_telegram(),
        _check_docker(),
        _check_system(),
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_res,
        "redis": redis_res,
        "telegram": tg_res,
        "containers": docker_res,
        "system": sys_res,
    }


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
    from sqlalchemy import or_
    result = await session.execute(
        select(Report).where(Report.id == report_id, or_(Report.status == "rejected", Report.status == "expired"))
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(404, detail="report not found")
    report.status = "published"
    report.reject_reason = None
    session.add(ModerationLog(report_id=report_id, moderator_id=moderator_id, action="restore", comment=None))
    await session.commit()
    return {"id": report_id, "status": "published"}


# ── helpers ──────────────────────────────────────────────────────────────────

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


# ── health check helpers ──────────────────────────────────────────────────────

async def _check_db(session: AsyncSession) -> dict:
    t0 = time.monotonic()
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:120]}


async def _check_redis() -> dict:
    import redis.asyncio as aioredis
    t0 = time.monotonic()
    try:
        client = aioredis.from_url(get_settings().redis_url, socket_timeout=4)
        await client.ping()
        await client.aclose()
        return {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:120]}


def _telegram_sync() -> dict:
    t0 = time.monotonic()
    try:
        urllib.request.urlopen("https://api.telegram.org", timeout=8)
        return {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:
        return {"status": "error", "latency_ms": round((time.monotonic() - t0) * 1000), "detail": str(e)[:120]}


async def _check_telegram() -> dict:
    return await asyncio.to_thread(_telegram_sync)


class _UnixHTTPConn(http.client.HTTPConnection):
    def __init__(self, path: str):
        super().__init__("localhost")
        self._path = path

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        self.sock = s


def _docker_sync() -> list[dict]:
    conn = _UnixHTTPConn(DOCKER_SOCKET)
    conn.request("GET", "/v1.43/containers/json?all=true")
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    result = []
    for c in data:
        name = c.get("Names", ["?"])[0].lstrip("/")
        result.append({
            "name": name,
            "status": c.get("Status", "unknown"),
            "running": c.get("State") == "running",
        })
    return sorted(result, key=lambda x: x["name"])


async def _check_docker() -> list[dict]:
    try:
        import os
        if not os.path.exists(DOCKER_SOCKET):
            return [{"name": "docker", "status": "socket not mounted", "running": False}]
        return await asyncio.to_thread(_docker_sync)
    except Exception as e:
        return [{"name": "docker", "status": f"error: {e}", "running": False}]


def _system_info_sync() -> dict:
    import shutil
    result: dict = {}
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
        result["load_avg"] = {"1m": float(parts[0]), "5m": float(parts[1]), "15m": float(parts[2])}
    except Exception:
        result["load_avg"] = None
    try:
        mem: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                p = line.split()
                if len(p) >= 2:
                    mem[p[0].rstrip(":")] = int(p[1])
        total = mem.get("MemTotal", 0) * 1024
        available = mem.get("MemAvailable", 0) * 1024
        used = total - available
        result["memory"] = {
            "total_mb": round(total / 1024**2),
            "used_mb": round(used / 1024**2),
            "available_mb": round(available / 1024**2),
            "percent": round(used / total * 100, 1) if total else 0,
        }
    except Exception:
        result["memory"] = None
    try:
        usage = shutil.disk_usage("/")
        result["disk"] = {
            "total_gb": round(usage.total / 1024**3, 1),
            "used_gb": round(usage.used / 1024**3, 1),
            "free_gb": round(usage.free / 1024**3, 1),
            "percent": round(usage.used / usage.total * 100, 1),
        }
    except Exception:
        result["disk"] = None
    return result


async def _check_system() -> dict:
    return await asyncio.to_thread(_system_info_sync)


# ── container logs ────────────────────────────────────────────────────────────

@router.get("/logs/{container}")
async def container_logs(container: str, tail: int = 100) -> list[str]:
    import os
    if not os.path.exists(DOCKER_SOCKET):
        return ["[docker socket not available]"]
    try:
        return await asyncio.to_thread(_fetch_docker_logs, container, tail)
    except Exception as e:
        return [f"[error: {e}]"]


def _fetch_docker_logs(container: str, tail: int) -> list[str]:
    conn = _UnixHTTPConn(DOCKER_SOCKET)
    conn.request(
        "GET",
        f"/v1.43/containers/{container}/logs?stdout=1&stderr=1&tail={tail}&timestamps=0&follow=0",
    )
    resp = conn.getresponse()
    raw = resp.read()
    conn.close()
    lines: list[str] = []
    i = 0
    while i < len(raw):
        if i + 8 > len(raw):
            break
        frame_size = int.from_bytes(raw[i + 4: i + 8], "big")
        i += 8
        if frame_size == 0:
            continue
        if i + frame_size > len(raw):
            break
        chunk = raw[i: i + frame_size].decode("utf-8", errors="replace")
        for line in chunk.splitlines():
            if line:
                lines.append(line)
        i += frame_size
    return lines
