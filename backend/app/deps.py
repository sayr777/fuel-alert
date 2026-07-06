from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()


async def require_moderator(x_moderator_token: str = Header(...)) -> str:
    """Minimal shared-secret auth for the moderation queue.

    Good enough for a single small moderation team at MVP stage; swap for real
    per-moderator accounts (and log moderator identity, not just the token)
    before opening this up to more than a handful of trusted people.
    """
    if x_moderator_token != settings.moderator_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid moderator token")
    return x_moderator_token
