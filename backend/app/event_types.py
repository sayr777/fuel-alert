"""Canonical dictionary of report event types.

This is the single source of truth for the classifier described in docs/event_types.md.
The bot and frontend both read this list via GET /api/v1/event-types instead of hardcoding it.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventTypeDef:
    code: str
    label_ru: str
    color: str
    requires_moderation: bool
    ttl_hours: int
    # Extra attributes the bot should collect for this event type, beyond the
    # common fields (geo, photos, description, event_at) that every report has.
    attributes: list[str] = field(default_factory=list)


EVENT_TYPES: dict[str, EventTypeDef] = {
    "NO_FUEL": EventTypeDef(
        code="NO_FUEL",
        label_ru="Топливо отсутствует",
        color="#FF4B3E",
        requires_moderation=False,
        ttl_hours=24,
        attributes=["fuel_grades"],
    ),
    "FUEL_AVAILABLE": EventTypeDef(
        code="FUEL_AVAILABLE",
        label_ru="Топливо появилось / в наличии",
        color="#3DDC84",
        requires_moderation=False,
        ttl_hours=12,
        attributes=["fuel_grades", "price"],
    ),
    "LIMITED_SALE": EventTypeDef(
        code="LIMITED_SALE",
        label_ru="Ограничение отпуска (лимит в одни руки)",
        color="#FFB020",
        requires_moderation=False,
        ttl_hours=24,
        attributes=["fuel_grades", "limit_liters"],
    ),
    "LONG_QUEUE": EventTypeDef(
        code="LONG_QUEUE",
        label_ru="Большая очередь на АЗС",
        color="#5B8CFF",
        requires_moderation=False,
        ttl_hours=6,
        attributes=["wait_minutes"],
    ),
    "OVERPRICE": EventTypeDef(
        code="OVERPRICE",
        label_ru="Завышенная цена",
        color="#FF7A1A",
        requires_moderation=False,
        ttl_hours=48,
        attributes=["fuel_grades", "price"],
    ),
    "ILLEGAL_SALE": EventTypeDef(
        code="ILLEGAL_SALE",
        label_ru="Незаконная торговля топливом (с рук, канистры, нелегальная точка)",
        color="#C554FF",
        requires_moderation=True,
        ttl_hours=24 * 30,
        attributes=["description"],
    ),
    "SHORT_MEASURE": EventTypeDef(
        code="SHORT_MEASURE",
        label_ru="Подозрение на недолив",
        color="#35C8E8",
        requires_moderation=True,
        ttl_hours=24 * 7,
        attributes=["fuel_grades", "pump_number"],
    ),
    "FAKE_FUEL": EventTypeDef(
        code="FAKE_FUEL",
        label_ru="Подозрение на контрафактное / некачественное топливо",
        color="#FF4FA0",
        requires_moderation=True,
        ttl_hours=24 * 7,
        attributes=["fuel_grades"],
    ),
    "STATION_CLOSED": EventTypeDef(
        code="STATION_CLOSED",
        label_ru="АЗС закрыта / не работает",
        color="#8A939E",
        requires_moderation=False,
        ttl_hours=24,
        attributes=["reason"],
    ),
    "FRAUD": EventTypeDef(
        code="FRAUD",
        label_ru="Мошенничество (оплата без отпуска, фейковые онлайн-продавцы)",
        color="#7C3AED",
        requires_moderation=True,
        ttl_hours=24 * 30,
        attributes=["description", "link"],
    ),
}

FUEL_GRADES = ["AI92", "AI95", "AI98", "AI100", "DT", "GAS"]


def get_event_type(code: str) -> EventTypeDef | None:
    return EVENT_TYPES.get(code)
