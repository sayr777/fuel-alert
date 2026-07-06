from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    fuel_grades: Mapped[list[str] | None] = mapped_column(ARRAY(String(8)), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    # Type-specific attributes that don't warrant their own column:
    # limit_liters, wait_minutes, pump_number, reason, link
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    station_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("stations.id"), nullable=True)

    # pending -> published | rejected | expired | duplicate
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Set when the validation pipeline folds this report into an earlier one
    # (same user/type within dedup_radius_m and dedup_window_minutes).
    duplicate_of: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("reports.id"), nullable=True)
    # Denormalized counter on the "canonical" report, bumped each time a
    # duplicate or an explicit /confirm comes in — avoids a COUNT(*) join on read.
    confirmations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_msg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Review flags raised by the automatic pipeline for the moderator queue,
    # e.g. ["exif_gps_mismatch", "exif_time_mismatch"] — independent of requires_moderation.
    review_flags: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)), nullable=True)


class ReportPhoto(Base):
    __tablename__ = "report_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reports.id"), nullable=False, index=True)
    s3_key: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    exif_taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exif_gps = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
