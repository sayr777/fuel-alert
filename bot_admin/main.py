import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config import get_settings
from handlers import router
from notifier import run_notifier
from watchdog import run_watchdog

logging.basicConfig(level=logging.INFO)
settings = get_settings()


async def main() -> None:
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    bot = Bot(token=settings.admin_bot_token)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    try:
        await asyncio.gather(
            dp.start_polling(bot),
            run_watchdog(bot),
            run_notifier(bot, redis),
        )
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
