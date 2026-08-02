import asyncio
import json
import logging

from aiogram import Bot
from redis.asyncio import Redis

from config import get_settings
from keyboards import moderation_keyboard

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_notifier(bot: Bot, redis: Redis) -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe("admin:new_report")
    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            data = json.loads(msg["data"])
            await _send_card(bot, data)
        except Exception:
            logger.exception("notifier error")


async def _send_card(bot: Bot, data: dict) -> None:
    report_id = data["id"]
    lines = [
        f"🆕 Новый репорт #{report_id}",
        f"Тип: {data.get('event_type_label', data.get('event_type', '?'))}",
    ]
    if data.get("fuel_grades"):
        lines.append(f"⛽ Топливо: {', '.join(data['fuel_grades'])}")
    if lat := data.get("lat"):
        lines.append(f"📍 {lat:.5f}, {data.get('lon', 0):.5f}")
    if data.get("description"):
        lines.append(f"💬 {data['description']}")
    if data.get("username"):
        lines.append(f"👤 @{data['username']}")
    await bot.send_message(
        settings.admin_chat_id,
        "\n".join(lines),
        reply_markup=moderation_keyboard(report_id),
    )
