import asyncio
import json
import logging
from datetime import datetime, timezone

import aiohttp
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle import GroupEventType

from api_client import ApiClient
from config import get_settings
from fsm import VkFSM
from keyboards import (
    GRADE_LABELS,
    main_menu_keyboard,
    event_type_keyboard,
    fuel_grades_keyboard,
    location_keyboard,
    skip_photos_keyboard,
    skip_comment_keyboard,
    confirm_keyboard,
)
from states import ReportState

logging.basicConfig(level=logging.INFO)
settings = get_settings()

bot = Bot(token=settings.vk_group_token)
api_client = ApiClient(settings.api_base_url)

from redis.asyncio import Redis as AioRedis
_redis: AioRedis | None = None
_fsm: VkFSM | None = None


async def get_fsm() -> VkFSM:
    global _redis, _fsm
    if _fsm is None:
        _redis = AioRedis.from_url(settings.redis_url)
        _fsm = VkFSM(_redis)
    return _fsm


STATUS_MESSAGES = {
    "published": "✅ Отчёт опубликован на карте!",
    "pending": "⏳ Отчёт принят и ожидает проверки модератором.",
    "duplicate": "ℹ️ Похожий отчёт уже есть — ваш подтвердил его.",
}


@bot.on.message(text=["Начать", "/start", "начать"])
async def on_start(message: Message):
    fsm = await get_fsm()
    user_id = message.from_id
    await api_client.register_user(user_id, f"vk_{user_id}")
    await fsm.clear(user_id)
    await message.answer(
        "👋 Добро пожаловать в Топливный Дозор!\n\n"
        "Сообщайте о проблемах с топливом на АЗС, помогайте другим водителям.\n"
        "Карта: https://dozor-fuel.online",
        keyboard=main_menu_keyboard(),
    )


@bot.on.message(text="ℹ️ Помощь")
async def on_help(message: Message):
    await message.answer(
        "🗺 Топливный Дозор — карта топливных проблем.\n\n"
        "📢 Сообщить о ситуации — начать репорт\n"
        "💡 Пожелание — написать предложение\n\n"
        "Карта: https://dozor-fuel.online",
        keyboard=main_menu_keyboard(),
    )


@bot.on.message(text="📢 Сообщить о ситуации")
async def on_report_start(message: Message):
    fsm = await get_fsm()
    user_id = message.from_id
    event_types = await api_client.get_event_types()
    await fsm.clear(user_id)
    await fsm.set_state(user_id, ReportState.CHOOSING_TYPE)
    await fsm.update_data(user_id, event_types={et["code"]: et for et in event_types})
    await message.answer("Выберите тип события:", keyboard=event_type_keyboard(event_types))


@bot.on.message(text="💡 Пожелание")
async def on_feedback_start(message: Message):
    fsm = await get_fsm()
    await fsm.set_state(message.from_id, "entering_feedback")
    await message.answer("Напишите ваше пожелание или предложение по улучшению сервиса:")


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def on_callback(event: MessageEvent):
    fsm = await get_fsm()
    user_id = event.user_id
    payload = event.payload or {}
    action = payload.get("action")

    if action == "cancel":
        await fsm.clear(user_id)
        await bot.api.messages.send(
            user_id=user_id,
            message="Отменено. Главное меню:",
            keyboard=main_menu_keyboard(),
            random_id=0,
        )
        await event.show_snackbar("Отменено")
        return

    if action == "etype":
        await _handle_event_type(event, fsm, user_id, payload.get("code"))
        return

    if action == "grade":
        await _handle_grade_toggle(event, fsm, user_id, payload.get("code"))
        return

    if action == "grades_done":
        await _handle_grades_done(event, fsm, user_id)
        return

    if action == "confirm":
        await _handle_confirm(event, fsm, user_id)
        return


async def _handle_event_type(event: MessageEvent, fsm: VkFSM, user_id: int, code: str):
    data = await fsm.get_data(user_id)
    event_types = data.get("event_types", {})
    if code == "OTHER":
        await fsm.update_data(user_id, event_type="OTHER", event_type_label="Другое", event_types=None)
        await fsm.set_state(user_id, ReportState.ENTERING_DESCRIPTION)
        await bot.api.messages.edit(
            peer_id=event.peer_id,
            message_id=event.conversation_message_id,
            message="✏️ Опишите ситуацию:",
        )
        await event.show_snackbar("Введите описание в чат")
        return

    et = event_types.get(code, {})
    attrs = et.get("attributes", [])
    await fsm.update_data(user_id, event_type=code, event_type_label=et.get("label_ru", code), event_types=None)

    if "fuel_grades" in attrs:
        grades = await api_client.get_fuel_grades()
        await fsm.update_data(user_id, available_grades=grades, selected_grades=[])
        await fsm.set_state(user_id, ReportState.CHOOSING_GRADES)
        await bot.api.messages.edit(
            peer_id=event.peer_id,
            message_id=event.conversation_message_id,
            message=f"Выбрано: {et.get('label_ru', code)}\n\n⛽ Выберите марку(и) топлива:",
            keyboard=fuel_grades_keyboard(grades, set()),
        )
    else:
        await fsm.set_state(user_id, ReportState.WAITING_LOCATION)
        await bot.api.messages.edit(
            peer_id=event.peer_id,
            message_id=event.conversation_message_id,
            message=f"Выбрано: {et.get('label_ru', code)}",
        )
        await bot.api.messages.send(
            user_id=user_id,
            message="📍 Отправьте геолокацию АЗС или нажмите «Пропустить»:",
            keyboard=location_keyboard(),
            random_id=0,
        )
    await event.show_snackbar("✓")


async def _handle_grade_toggle(event: MessageEvent, fsm: VkFSM, user_id: int, grade: str):
    data = await fsm.get_data(user_id)
    selected = set(data.get("selected_grades", []))
    selected.symmetric_difference_update({grade})
    await fsm.update_data(user_id, selected_grades=list(selected))
    grades = data.get("available_grades", [])
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        message_id=event.conversation_message_id,
        message=event.object.message.text if hasattr(event.object, "message") else "⛽ Выберите марки топлива:",
        keyboard=fuel_grades_keyboard(grades, selected),
    )
    await event.show_snackbar("✓")


async def _handle_grades_done(event: MessageEvent, fsm: VkFSM, user_id: int):
    data = await fsm.get_data(user_id)
    selected = set(data.get("selected_grades", []))
    if not selected:
        await event.show_snackbar("Выберите хотя бы одну марку!")
        return
    labels = ", ".join(GRADE_LABELS.get(g, g) for g in selected)
    await fsm.update_data(user_id, fuel_grades=list(selected), selected_grades=None, available_grades=None)
    await fsm.set_state(user_id, ReportState.WAITING_LOCATION)
    await bot.api.messages.send(
        user_id=user_id,
        message=f"Топливо: {labels}\n\n📍 Отправьте геолокацию АЗС или нажмите «Пропустить»:",
        keyboard=location_keyboard(),
        random_id=0,
    )
    await event.show_snackbar("✓")


async def _handle_confirm(event: MessageEvent, fsm: VkFSM, user_id: int):
    data = await fsm.get_data(user_id)
    photos_raw = data.get("photos", [])
    photos = []
    if photos_raw:
        async with aiohttp.ClientSession() as session:
            for url in photos_raw:
                async with session.get(url) as r:
                    photos.append(("photo.jpg", await r.read()))
    try:
        result = await api_client.submit_report(
            vk_id=user_id,
            event_type=data["event_type"],
            lat=data.get("lat", 0.0),
            lon=data.get("lon", 0.0),
            event_at=datetime.now(timezone.utc),
            fuel_grades=data.get("fuel_grades"),
            description=data.get("description"),
            photos=photos if photos else None,
        )
        status = result.get("status", "unknown")
        text = STATUS_MESSAGES.get(status, f"Статус: {status}")
    except Exception:
        text = "❌ Ошибка при отправке. Попробуйте позже."

    await fsm.clear(user_id)
    await bot.api.messages.send(
        user_id=user_id,
        message=text + "\n\nГлавное меню:",
        keyboard=main_menu_keyboard(),
        random_id=0,
    )
    await event.show_snackbar("Отправлено!")


@bot.on.message()
async def on_any_message(message: Message):
    fsm = await get_fsm()
    user_id = message.from_id
    state = await fsm.get_state(user_id)

    # Handle geo attachment
    if message.geo and state == ReportState.WAITING_LOCATION:
        lat = message.geo.coordinates.latitude
        lon = message.geo.coordinates.longitude
        await fsm.update_data(user_id, lat=lat, lon=lon)
        await fsm.set_state(user_id, ReportState.WAITING_PHOTOS)
        await message.answer(
            f"📍 Геолокация принята: {lat:.5f}, {lon:.5f}\n\n"
            "📷 Отправьте фото (до 2 шт) или нажмите «Пропустить фото»:",
            keyboard=skip_photos_keyboard(),
        )
        return

    # Handle photo attachments
    if message.attachments and state == ReportState.WAITING_PHOTOS:
        for att in message.attachments:
            if att.type.value == "photo":
                data = await fsm.get_data(user_id)
                photos = data.get("photos", [])
                if len(photos) >= 2:
                    await message.answer("Максимум 2 фото. Нажмите «⏭ Пропустить фото».")
                    return
                # Get largest photo size
                sizes = sorted(
                    att.photo.sizes,
                    key=lambda s: s.width * s.height if s.width and s.height else 0,
                )
                url = sizes[-1].url if sizes else None
                if url:
                    photos.append(url)
                    await fsm.update_data(user_id, photos=photos)
                if len(photos) >= 2:
                    await fsm.set_state(user_id, ReportState.ENTERING_COMMENT)
                    await message.answer(
                        "Фото 2/2 принято.\n\n💬 Добавьте комментарий (необязательно):",
                        keyboard=skip_comment_keyboard(),
                    )
                else:
                    await message.answer(f"Фото {len(photos)}/2. Ещё одно или «⏭ Пропустить фото».")
                return

    if not state:
        await message.answer("Используйте меню ниже:", keyboard=main_menu_keyboard())
        return

    text = message.text or ""

    if state == ReportState.WAITING_LOCATION:
        if text == "📍 Пропустить геолокацию":
            await fsm.update_data(user_id, lat=0.0, lon=0.0)
            await fsm.set_state(user_id, ReportState.WAITING_PHOTOS)
            await message.answer(
                "📷 Отправьте фото (до 2 шт) или нажмите «Пропустить фото»:",
                keyboard=skip_photos_keyboard(),
            )
        else:
            await message.answer(
                "📍 Пожалуйста, отправьте геолокацию или нажмите «📍 Пропустить геолокацию»."
            )
        return

    if state == ReportState.WAITING_PHOTOS:
        if text == "⏭ Пропустить фото":
            await fsm.set_state(user_id, ReportState.ENTERING_COMMENT)
            await message.answer(
                "💬 Добавьте комментарий (необязательно):",
                keyboard=skip_comment_keyboard(),
            )
        else:
            await message.answer("Отправьте фото или нажмите «⏭ Пропустить фото».")
        return

    if state == ReportState.ENTERING_COMMENT:
        if text == "⏭ Без комментария":
            await _show_confirmation(message, fsm, user_id)
        elif text:
            await fsm.update_data(user_id, description=text)
            await _show_confirmation(message, fsm, user_id)
        else:
            await message.answer("Напишите комментарий или нажмите «⏭ Без комментария».")
        return

    if state == ReportState.ENTERING_DESCRIPTION:
        if text:
            await fsm.update_data(user_id, description=text)
            await fsm.set_state(user_id, ReportState.WAITING_LOCATION)
            await message.answer("📍 Отправьте геолокацию АЗС:", keyboard=location_keyboard())
        else:
            await message.answer("Пожалуйста, напишите описание текстом.")
        return

    if state == "entering_feedback":
        if text:
            await message.answer(
                "Спасибо за пожелание! Мы обязательно его рассмотрим. 🙏",
                keyboard=main_menu_keyboard(),
            )
            await fsm.clear(user_id)
        else:
            await message.answer("Пожалуйста, напишите пожелание текстом.")
        return

    await message.answer("Используйте меню ниже:", keyboard=main_menu_keyboard())


async def _show_confirmation(message: Message, fsm: VkFSM, user_id: int):
    data = await fsm.get_data(user_id)
    photos = data.get("photos", [])
    lines = [f"Тип: {data.get('event_type_label', data.get('event_type'))}"]
    lat, lon = data.get("lat", 0), data.get("lon", 0)
    if lat or lon:
        lines.append(f"Координаты: {lat:.5f}, {lon:.5f}")
    if data.get("fuel_grades"):
        labels = ", ".join(GRADE_LABELS.get(g, g) for g in data["fuel_grades"])
        lines.append(f"Топливо: {labels}")
    if data.get("description"):
        lines.append(f"Комментарий: {data['description']}")
    if photos:
        lines.append(f"Фото: {len(photos)} шт.")
    await fsm.set_state(user_id, ReportState.CONFIRMING)
    await message.answer("\n".join(lines) + "\n\nВсё верно?", keyboard=confirm_keyboard())


if __name__ == "__main__":
    bot.run_forever()
