from pydantic import BaseModel


class EventTypeOut(BaseModel):
    code: str
    label_ru: str
    color: str
    requires_moderation: bool
    ttl_hours: int
    attributes: list[str]
