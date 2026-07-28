import asyncio
import logging

from redis.asyncio import from_url as redis_from_url

from api_client import ApiClient
from client import MaxClient
from config import get_settings
from fsm import MaxFSM
from handlers import dispatch_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    redis = redis_from_url(settings.redis_url, decode_responses=False)
    client = MaxClient(settings.max_bot_token)
    api = ApiClient()
    fsm = MaxFSM(redis)

    try:
        await client.set_commands([
            {"name": "start", "description": "Начало работы / главное меню"},
            {"name": "help", "description": "Справка по использованию бота"},
        ])
        logger.info("Bot commands registered")
    except Exception:
        logger.warning("Could not register bot commands", exc_info=True)

    logger.info("MAX bot started, long polling…")
    marker: int | None = None

    try:
        while True:
            try:
                data = await client.get_updates(marker=marker, timeout=30)
                updates: list[dict] = data.get("updates", [])
                new_marker = data.get("marker")
                if new_marker is not None:
                    marker = new_marker
                for upd in updates:
                    try:
                        await dispatch_update(upd, client, api, fsm)
                    except Exception:
                        logger.exception("Error handling update: %s", upd.get("update_type"))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Polling error, retrying in 5 s")
                await asyncio.sleep(5)
    finally:
        await client.close()
        await api.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
