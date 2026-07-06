import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from api_client import ApiClient
from config import get_settings
from handlers import router

logging.basicConfig(level=logging.INFO)
settings = get_settings()


async def main() -> None:
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    bot = Bot(token=settings.bot_token)
    api = ApiClient()

    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    try:
        await dp.start_polling(bot, api=api)
    finally:
        await api.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())