from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()


async def require_moderator(authorization: str = Header(...)) -> str:
    """Minimal shared-secret auth for the moderation queue."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != settings.moderator_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid moderator token")
    return token
