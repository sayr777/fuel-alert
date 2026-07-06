import random

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.user import UserOut, UserRegister

router = APIRouter(tags=["users"])


def _generate_nickname() -> str:
    return f"Водитель-{random.randint(1000, 9999)}"


@router.post("/users/register", response_model=UserOut)
async def register_user(payload: UserRegister, session: AsyncSession = Depends(get_session)) -> User:
    """Upserts a user by telegram_id — called from the bot's /start handler."""
    result = await session.execute(select(User).where(User.telegram_id == payload.telegram_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        telegram_id=payload.telegram_id,
        nickname=payload.nickname or _generate_nickname(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
