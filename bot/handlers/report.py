import json
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient
from keyboards import (
    GRADE_LABELS,
    confirm_keyboard,
    event_type_keyboard,
    fuel_grades_keyboard,
    location_keyboard,
    main_menu_keyboard,
    skip_keyboard,
)
from states import ReportFlow

router = Router()

ATTRIBUTE_PROMPTS = {
    "price": ("💰 Введите цену за литр (число, например 68.5):", ReportFlow.entering_price),
    "limit_liters": ("⛽ Введите лимит отпуска в литрах:", ReportFlow.entering_limit),
    "wait_minutes": ("⏱ Введите примерное время ожидания в минутах:", ReportFlow.entering_wait),
    "pump_number": ("🔢 Введите номер колонки:", ReportFlow.entering_pump),
    "reason": ("📝 Укажите причину (например: ремонт, нет электричества):", ReportFlow.entering_reason),
    "link": ("🔗 Вставьте ссылку (если есть):", ReportFlow.entering_link),
    "description": ("📝 Опишите ситуацию подробнее:", ReportFlow.entering_description),
}

STATUS_MESSAGES = {
    "published": "✅ Отчёт опубликован на карте!",
    "pending": "⏳ Отчёт принят и ожидает проверки модератором.",
    "duplicate": "ℹ️ Похожий отчёт уже есть — ваш подтвердил его.",
    "rejected": "❌ Отчёт отклонён: {reason}",
}


@router.message(F.text == "📢 Сообщить о ситуации")
async def start_report(message: Message, state: FSMContext, api: ApiClient) -> None:
    event_types = await api.get_event_types()
    await state.set_state(ReportFlow.choosing_type)
    await state.update_data(event_types={et["code"]: et for et in event_types})
    await message.answer("Выберите тип события:", reply_markup=event_type_keyboard(event_types))


@router.callback_query(F.data == "cancel")
async def cancel_report(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(ReportFlow.choosing_type, F.data.startswith("etype:"))
async def on_event_type(callback: CallbackQuery, state: FSMContext, api: ApiClient) -> None:
    code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    event_type = data["event_types"][code]
    await state.update_data(event_type=code, event_type_label=event_type["label_ru"], extra={})

    attrs = [a for a in event_type["attributes"] if a != "description"]
    if "fuel_grades" in attrs:
        grades = await api.get_fuel_grades()
        await state.update_data(pending_attrs=attrs[1:], selected_grades=set())
        await state.set_state(ReportFlow.choosing_grades)
        await callback.message.edit_text(
            "Выберите марки топлива (можно несколько):",
            reply_markup=fuel_grades_keyboard(grades, set()),
        )
    else:
        await state.update_data(pending_attrs=attrs)
        await _advance_to_next_attr(callback.message, state)
    await callback.answer()


@router.callback_query(ReportFlow.choosing_grades, F.data.startswith("grade:"))
async def toggle_grade(callback: CallbackQuery, state: FSMContext, api: ApiClient) -> None:
    grade = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected: set[str] = set(data.get("selected_grades", set()))
    if grade in selected:
        selected.discard(grade)
    else:
        selected.add(grade)
    await state.update_data(selected_grades=selected)
    grades = await api.get_fuel_grades()
    await callback.message.edit_reply_markup(reply_markup=fuel_grades_keyboard(grades, selected))
    await callback.answer()


@router.callback_query(ReportFlow.choosing_grades, F.data == "grades:done")
async def grades_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected: set[str] = data.get("selected_grades", set())
    if not selected:
        await callback.answer("Выберите хотя бы одну марку", show_alert=True)
        return
    await state.update_data(fuel_grades=list(selected))
    await _advance_to_next_attr(callback.message, state)
    await callback.answer()


@router.message(ReportFlow.entering_price)
async def on_price(message: Message, state: FSMContext) -> None:
    try:
        price = float(message.text.replace(",", "."))
    except (ValueError, AttributeError):
        await message.answer("Введите число, например 68.5")
        return
    await state.update_data(price=price)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_limit)
async def on_limit(message: Message, state: FSMContext) -> None:
    try:
        liters = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Введите целое число литров")
        return
    data = await state.get_data()
    extra = data.get("extra", {})
    extra["limit_liters"] = liters
    await state.update_data(extra=extra)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_wait)
async def on_wait(message: Message, state: FSMContext) -> None:
    try:
        minutes = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Введите целое число минут")
        return
    data = await state.get_data()
    extra = data.get("extra", {})
    extra["wait_minutes"] = minutes
    await state.update_data(extra=extra)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_pump)
async def on_pump(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    extra = data.get("extra", {})
    extra["pump_number"] = message.text.strip()
    await state.update_data(extra=extra)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_reason)
async def on_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    extra = data.get("extra", {})
    extra["reason"] = message.text.strip()
    await state.update_data(extra=extra)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_link)
async def on_link(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    extra = data.get("extra", {})
    extra["link"] = message.text.strip()
    await state.update_data(extra=extra)
    await _advance_to_next_attr(message, state)


@router.message(ReportFlow.entering_description)
async def on_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await _go_to_location(message, state)


@router.message(ReportFlow.waiting_location, F.location)
async def on_location(message: Message, state: FSMContext) -> None:
    await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    await state.set_state(ReportFlow.waiting_photos)
    await message.answer(
        "📷 Отправьте фото как *файл* (не сжатое) — так сохранится EXIF.\n"
        "Можно до 2 фото. Когда готовы — нажмите «Пропустить».",
        parse_mode="Markdown",
        reply_markup=skip_keyboard("Пропустить фото →"),
    )


@router.message(ReportFlow.waiting_photos, F.document)
async def on_photo_file(message: Message, state: FSMContext) -> None:
    if not message.document.mime_type or not message.document.mime_type.startswith("image/"):
        await message.answer("Отправьте изображение как файл.")
        return
    data = await state.get_data()
    photos: list[dict] = data.get("photos", [])
    if len(photos) >= 2:
        await message.answer("Максимум 2 фото. Нажмите «Пропустить» для продолжения.")
        return
    file = await message.bot.get_file(message.document.file_id)
    downloaded = await message.bot.download_file(file.file_path)
    photos.append({"filename": message.document.file_name or "photo.jpg", "data": downloaded.read()})
    await state.update_data(photos=photos)
    await message.answer(f"Фото {len(photos)}/2 добавлено. Ещё одно или «Пропустить».")


@router.callback_query(ReportFlow.waiting_photos, F.data == "skip")
async def photos_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    event_type = data["event_types"][data["event_type"]]
    if "description" in event_type["attributes"] and "description" not in data:
        await state.set_state(ReportFlow.entering_description)
        await callback.message.edit_text("📝 Опишите ситуацию подробнее:")
    else:
        await _show_confirmation(callback.message, state)
    await callback.answer()


@router.callback_query(ReportFlow.confirming, F.data == "confirm:send")
async def confirm_send(callback: CallbackQuery, state: FSMContext, api: ApiClient) -> None:
    data = await state.get_data()
    photos_raw = data.get("photos", [])
    photos = [(p["filename"], p["data"]) for p in photos_raw] if photos_raw else None

    try:
        result = await api.submit_report(
            telegram_id=callback.from_user.id,
            event_type=data["event_type"],
            lat=data["lat"],
            lon=data["lon"],
            event_at=datetime.now(timezone.utc),
            fuel_grades=data.get("fuel_grades"),
            description=data.get("description"),
            price=data.get("price"),
            extra=data.get("extra") or None,
            photos=photos,
        )
    except Exception:
        await callback.message.edit_text("❌ Ошибка при отправке. Попробуйте позже.")
        await state.clear()
        await callback.answer()
        return

    status = result.get("status", "unknown")
    if status == "rejected":
        text = STATUS_MESSAGES["rejected"].format(reason=result.get("reject_reason", "неизвестно"))
    else:
        text = STATUS_MESSAGES.get(status, f"Статус: {status}")
        if status == "duplicate" and result.get("duplicate_of"):
            text += f" (отчёт #{result['duplicate_of']})"

    await callback.message.edit_text(text)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await state.clear()
    await callback.answer()


async def _advance_to_next_attr(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    pending: list[str] = data.get("pending_attrs", [])
    if not pending:
        await _go_to_location(message, state)
        return

    attr = pending[0]
    await state.update_data(pending_attrs=pending[1:])
    prompt, flow_state = ATTRIBUTE_PROMPTS[attr]
    await state.set_state(flow_state)
    await message.answer(prompt)


async def _go_to_location(message: Message, state: FSMContext) -> None:
    await state.set_state(ReportFlow.waiting_location)
    await message.answer("📍 Отправьте геолокацию АЗС:", reply_markup=location_keyboard())


async def _show_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lines = [
        f"Тип: {data['event_type_label']}",
        f"Координаты: {data['lat']:.5f}, {data['lon']:.5f}",
    ]
    if data.get("fuel_grades"):
        labels = [GRADE_LABELS.get(g, g) for g in data["fuel_grades"]]
        lines.append(f"Топливо: {', '.join(labels)}")
    if data.get("price") is not None:
        lines.append(f"Цена: {data['price']} ₽/л")
    if data.get("description"):
        lines.append(f"Описание: {data['description']}")
    if data.get("extra"):
        lines.append(f"Дополнительно: {json.dumps(data['extra'], ensure_ascii=False)}")
    photos = data.get("photos", [])
    if photos:
        lines.append(f"Фото: {len(photos)}")

    await state.set_state(ReportFlow.confirming)
    await message.answer("\n".join(lines) + "\n\nВсё верно?", reply_markup=confirm_keyboard())