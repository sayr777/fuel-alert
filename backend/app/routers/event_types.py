from fastapi import APIRouter

from app.event_types import EVENT_TYPES, FUEL_GRADES
from app.schemas.event_type import EventTypeOut

router = APIRouter(tags=["event-types"])


@router.get("/event-types", response_model=list[EventTypeOut])
async def list_event_types() -> list[EventTypeOut]:
    return [EventTypeOut(**vars(e)) for e in EVENT_TYPES.values()]


@router.get("/fuel-grades", response_model=list[str])
async def list_fuel_grades() -> list[str]:
    return FUEL_GRADES
