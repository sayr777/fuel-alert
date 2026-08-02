from __future__ import annotations

from redis.asyncio import Redis

_redis: Redis | None = None


async def init_redis(url: str) -> None:
    global _redis
    _redis = Redis.from_url(url)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis | None:
    return _redis
