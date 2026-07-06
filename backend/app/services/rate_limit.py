import time

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def check_rate_limit(telegram_id: int) -> bool:
    """Sliding-window-ish rate limit: at most `rate_limit_per_hour` reports/hour/user.

    Returns True if the user is still within budget (and records this attempt).
    """
    redis = get_redis()
    key = f"ratelimit:reports:{telegram_id}"
    now = time.time()
    window_start = now - 3600

    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 3600)
        _, count, *_ = await pipe.execute()

    return count < settings.rate_limit_per_hour
