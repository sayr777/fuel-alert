from pydantic import BaseModel


class UserRegister(BaseModel):
    telegram_id: int
    nickname: str | None = None


class UserOut(BaseModel):
    id: int
    nickname: str
    trust_score: float
    is_banned: bool

    model_config = {"from_attributes": True}
