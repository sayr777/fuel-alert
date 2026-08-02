import asyncio
import logging

import aiohttp
from aiogram import Bot

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_watchdog(bot: Bot) -> None:
    prev: dict[str, bool] = {}
    while True:
        await asyncio.sleep(settings.health_interval)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.api_base_url}/moderation/health",
                    headers={"Authorization": f"Bearer {settings.moderator_token}"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json()
            checks: dict[str, bool] = {
                "🗄 База данных": data.get("database", {}).get("status") == "ok",
                "⚡ Redis": data.get("redis", {}).get("status") == "ok",
                "✈️ Telegram (VPN)": data.get("telegram", {}).get("status") == "ok",
            }
            for c in data.get("containers", []):
                checks[f"🐳 {c['name']}"] = c.get("status") == "running"
            for name, ok in checks.items():
                was = prev.get(name)
                if was is None:
                    prev[name] = ok
                    continue
                if was and not ok:
                    await bot.send_message(settings.admin_chat_id, f"🔴 АВАРИЯ: {name} НЕДОСТУПЕН")
                    prev[name] = False
                elif not was and ok:
                    await bot.send_message(settings.admin_chat_id, f"✅ ВОССТАНОВЛЕН: {name}")
                    prev[name] = True
        except Exception:
            logger.exception("watchdog error")
