from __future__ import annotations

import logging
from datetime import datetime, timezone

from api_client import ApiClient
from client import MaxClient
from fsm import MaxFSM
from handlers.start import HELP_TEXT
from keyboards import (
    GRADE_LABELS,
    comment_keyboard,
    confirm_keyboard,
    event_type_keyboard,
    fuel_grades_keyboard,
    location_keyboard,
    main_menu,
    photos_keyboard,
)
from states import (
    CHOOSING_GRADES,
    CHOOSING_TYPE,
    CONFIRMING,
    ENTERING_COMMENT,
    ENTERING_DESCRIPTION,
    WAITING_LOCATION,
    WAITING_PHOTOS,
)

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    "published": "✅ Обращение опубликовано на карте!",
    "pending": "⏳ Обращение принято и ожидает проверки модератором.",
    "duplicate": "ℹ️ Похожее обращение уже есть — ваше подтвердило его.",
    "rejected": "❌ Обращение отклонено: {reason}",
}


async def handle_callback(
    user_id: int,
    callback_id: str,
    payload: str,
    client: MaxClient,
    api: ApiClient,
    fsm: MaxFSM,
) -> None:
    state = await fsm.get_state(user_id)

    if payload == "cancel":
        await fsm.clear(user_id)
        await client.answer_callback(callback_id, text="Отменено.")
        await client.send_message(user_id, "Главное меню:", main_menu())
        return

    if payload == "help":
        await client.answer_callback(callback_id)
        await client.send_message(user_id, HELP_TEXT, main_menu())
        return

    if payload == "start_report":
        event_types = await api.get_event_types()
        await fsm.set_state(user_id, CHOOSING_TYPE)
        await fsm.update_data(user_id, event_types={et["code"]: et for et in event_types})
        await client.answer_callback(callback_id)
        await client.send_message(
            user_id,
            "Выберите тип события:",
            event_type_keyboard(event_types),
        )
        return

    if payload.startswith("etype:") and state == CHOOSING_TYPE:
        code = payload.split(":", 1)[1]
        data = await fsm.get_data(user_id)
        if code == "OTHER":
            await fsm.update_data(
                user_id,
                event_type="OTHER",
                event_type_label="Другое",
                event_types=None,
            )
            await fsm.set_state(user_id, ENTERING_DESCRIPTION)
            await client.answer_callback(callback_id, text="Выбрано: Другое\n\n✏️ Опишите ситуацию:")
            return

        et = data["event_types"].get(code)
        if not et:
            await client.answer_callback(callback_id)
            return

        attrs = et.get("attributes", [])
        await fsm.update_data(
            user_id,
            event_type=code,
            event_type_label=et["label_ru"],
            event_types=None,
        )

        if "fuel_grades" in attrs:
            grades = await api.get_fuel_grades()
            await fsm.update_data(user_id, available_grades=grades, selected_grades=[])
            await fsm.set_state(user_id, CHOOSING_GRADES)
            await client.answer_callback(
                callback_id,
                text=f"Выбрано: {et['label_ru']}\n\n⛽ Выберите марку(и) топлива:",
                keyboard=fuel_grades_keyboard(grades, set()),
            )
        else:
            await fsm.set_state(user_id, WAITING_LOCATION)
            await client.answer_callback(callback_id, text=f"Выбрано: {et['label_ru']}")
            await client.send_message(
                user_id,
                "📍 Отправьте геолокацию АЗС:",
                location_keyboard(),
            )
        return

    if payload.startswith("grade:") and state == CHOOSING_GRADES:
        grade = payload.split(":", 1)[1]
        data = await fsm.get_data(user_id)
        selected: set[str] = set(data.get("selected_grades", []))
        selected.symmetric_difference_update({grade})
        await fsm.update_data(user_id, selected_grades=list(selected))
        await client.answer_callback(
            callback_id,
            text=f"Выбрано: {data['event_type_label']}\n\n⛽ Выберите марку(и) топлива:",
            keyboard=fuel_grades_keyboard(data["available_grades"], selected),
        )
        return

    if payload == "grades_done" and state == CHOOSING_GRADES:
        data = await fsm.get_data(user_id)
        selected = set(data.get("selected_grades", []))
        if not selected:
            await client.answer_callback(callback_id)
            await client.send_message(user_id, "Выберите хотя бы одну марку топлива.")
            return
        labels = ", ".join(GRADE_LABELS.get(g, g) for g in selected)
        await fsm.update_data(
            user_id,
            fuel_grades=list(selected),
            selected_grades=None,
            available_grades=None,
        )
        await fsm.set_state(user_id, WAITING_LOCATION)
        await client.answer_callback(
            callback_id,
            text=f"Выбрано: {data['event_type_label']}\nТопливо: {labels}",
        )
        await client.send_message(user_id, "📍 Отправьте геолокацию АЗС:", location_keyboard())
        return

    if payload == "skip_photo" and state == WAITING_PHOTOS:
        await fsm.set_state(user_id, ENTERING_COMMENT)
        await client.answer_callback(callback_id)
        await client.send_message(
            user_id,
            "💬 Добавьте комментарий (необязательно):",
            comment_keyboard(),
        )
        return

    if payload == "skip_comment" and state == ENTERING_COMMENT:
        await client.answer_callback(callback_id)
        await _show_confirmation(user_id, client, fsm)
        return

    if payload == "confirm_send" and state == CONFIRMING:
        await client.answer_callback(callback_id)
        await _submit_report(user_id, client, api, fsm)
        return

    # Unknown payload or wrong state — ignore silently
    await client.answer_callback(callback_id)


async def handle_message(
    user_id: int,
    text: str,
    attachments: list[dict],
    client: MaxClient,
    api: ApiClient,
    fsm: MaxFSM,
) -> None:
    state = await fsm.get_state(user_id)

    # Location attachment (any state that expects it)
    location = _extract_location(attachments)
    if location and state == WAITING_LOCATION:
        lat, lon = location
        await fsm.update_data(user_id, lat=lat, lon=lon)
        await fsm.set_state(user_id, WAITING_PHOTOS)
        await client.send_message(
            user_id,
            "📷 Можно прикрепить до 2 фото, или нажмите «⏭ Пропустить фото».",
            photos_keyboard(),
        )
        return

    # Image attachment in photo step
    img_url = _extract_image_url(attachments)
    if img_url and state == WAITING_PHOTOS:
        data = await fsm.get_data(user_id)
        photos: list[str] = data.get("photo_urls", [])
        if len(photos) >= 2:
            await client.send_message(
                user_id,
                "Максимум 2 фото. Нажмите «⏭ Пропустить фото» для продолжения.",
            )
            return
        photos.append(img_url)
        await fsm.update_data(user_id, photo_urls=photos)
        if len(photos) < 2:
            await client.send_message(
                user_id,
                f"Фото {len(photos)}/2 принято. Ещё одно или «⏭ Пропустить фото».",
                photos_keyboard(),
            )
        else:
            await client.send_message(user_id, "Фото 2/2 принято.")
            await fsm.set_state(user_id, ENTERING_COMMENT)
            await client.send_message(
                user_id,
                "💬 Добавьте комментарий (необязательно):",
                comment_keyboard(),
            )
        return

    # Text in description step (OTHER event type)
    if text and state == ENTERING_DESCRIPTION:
        await fsm.update_data(user_id, description=text.strip())
        await fsm.set_state(user_id, WAITING_LOCATION)
        await client.send_message(user_id, "📍 Отправьте геолокацию АЗС:", location_keyboard())
        return

    # Text in comment step
    if text and state == ENTERING_COMMENT:
        await fsm.update_data(user_id, description=text.strip())
        await _show_confirmation(user_id, client, fsm)
        return

    # No active session — show main menu
    if state is None:
        await client.send_message(user_id, "Главное меню:", main_menu())
        return

    # Fallback: nudge user toward next expected action
    await _send_state_hint(user_id, state, client)


async def _show_confirmation(user_id: int, client: MaxClient, fsm: MaxFSM) -> None:
    data = await fsm.get_data(user_id)
    lines = [
        f"Тип: {data['event_type_label']}",
        f"Координаты: {data['lat']:.5f}, {data['lon']:.5f}",
    ]
    if data.get("fuel_grades"):
        labels = ", ".join(GRADE_LABELS.get(g, g) for g in data["fuel_grades"])
        lines.append(f"Топливо: {labels}")
    if data.get("description"):
        lines.append(f"Комментарий: {data['description']}")
    n_photos = len(data.get("photo_urls", []))
    if n_photos:
        lines.append(f"Фото: {n_photos} шт.")
    await fsm.set_state(user_id, CONFIRMING)
    await client.send_message(
        user_id,
        "\n".join(lines) + "\n\nВсё верно?",
        confirm_keyboard(),
    )


async def _submit_report(
    user_id: int,
    client: MaxClient,
    api: ApiClient,
    fsm: MaxFSM,
) -> None:
    data = await fsm.get_data(user_id)
    photo_urls: list[str] = data.get("photo_urls", [])
    photos: list[tuple[str, bytes]] | None = None
    if photo_urls:
        photos = []
        for i, url in enumerate(photo_urls):
            try:
                raw = await client.download_bytes(url)
                photos.append((f"photo_{i + 1}.jpg", raw))
            except Exception:
                logger.warning("Failed to download photo %s", url)

    try:
        result = await api.submit_report(
            user_id=user_id,
            event_type=data["event_type"],
            lat=data["lat"],
            lon=data["lon"],
            event_at=datetime.now(timezone.utc),
            fuel_grades=data.get("fuel_grades"),
            description=data.get("description"),
            photos=photos or None,
        )
    except Exception:
        logger.exception("submit_report failed for user %s", user_id)
        await client.send_message(user_id, "❌ Ошибка при отправке. Попробуйте позже.", main_menu())
        await fsm.clear(user_id)
        return

    status = result.get("status", "unknown")
    if status == "rejected":
        text = STATUS_MESSAGES["rejected"].format(reason=result.get("reject_reason", "неизвестно"))
    else:
        text = STATUS_MESSAGES.get(status, f"Статус: {status}")
        if status == "duplicate" and result.get("duplicate_of"):
            text += f" (обращение #{result['duplicate_of']})"

    await client.send_message(user_id, text, main_menu())
    await fsm.clear(user_id)


async def _send_state_hint(user_id: int, state: str, client: MaxClient) -> None:
    hints = {
        WAITING_LOCATION: ("📍 Нажмите кнопку «Отправить геолокацию».", location_keyboard()),
        WAITING_PHOTOS: ("📷 Отправьте фото или нажмите «⏭ Пропустить фото».", photos_keyboard()),
        ENTERING_COMMENT: ("💬 Напишите комментарий или нажмите «⏭ Без комментария».", comment_keyboard()),
        ENTERING_DESCRIPTION: ("✏️ Напишите описание ситуации текстом.", None),
    }
    if state in hints:
        msg, kb = hints[state]
        await client.send_message(user_id, msg, kb)


def _extract_location(attachments: list[dict]) -> tuple[float, float] | None:
    for att in attachments:
        if att.get("type") == "location":
            # MAX sends lat/lon at attachment root level, not inside payload
            lat = att.get("latitude")
            lon = att.get("longitude")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    return None


def _extract_image_url(attachments: list[dict]) -> str | None:
    for att in attachments:
        if att.get("type") in ("image", "photo"):
            payload = att.get("payload", {})
            url = payload.get("url") or payload.get("photo_url")
            if url:
                return str(url)
    return None
