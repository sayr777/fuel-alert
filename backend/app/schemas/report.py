from datetime import datetime

from pydantic import BaseModel


class ReportSubmitResult(BaseModel):
    """Returned to the bot right after ingestion, before any moderation happens."""

    id: int
    status: str  # pending | published | rejected | duplicate
    reject_reason: str | None = None
    duplicate_of: int | None = None
    confirmations_count: int | None = None


class PhotoOut(BaseModel):
    url: str
    taken_at: datetime | None = None


class ReportProperties(BaseModel):
    id: int
    event_type: str
    fuel_grades: list[str] | None
    description: str | None
    price: float | None
    extra: dict | None
    event_at: datetime
    nickname: str
    station_id: int | None
    photos: list[PhotoOut]
    confirmations_count: int
    review_flags: list[str] | None = None


class ReportFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: ReportProperties


class ReportFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[ReportFeature]
    next_cursor: str | None = None
