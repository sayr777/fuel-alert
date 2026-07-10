from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient
from keyboards import (
    confirm_keyboard,
    event_type_keyboard,
    location_keyboard,
    main_menu_keyboard,
    photos_keyboard,
)
from states import ReportFlow

router = Router()

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
async def on_event_type(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    event_type = data["event_types"][code]
    await state.update_data(event_type=code, event_type_label=event_type["label_ru"])
    await state.set_state(ReportFlow.waiting_location)
    await callback.message.edit_text(f"Выбрано: {event_type['label_ru']}")
    await callback.message.answer("📍 Отправьте геолокацию АЗС:", reply_markup=location_keyboard())
    await callback.answer()


@router.message(ReportFlow.waiting_location, F.location)
async def on_location(message: Message, state: FSMContext) -> None:
    await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    await state.set_state(ReportFlow.waiting_photos)
    await message.answer(
        "📷 Можно прикрепить до 2 фото (или нажмите «⏭ Пропустить фото»).",
        reply_markup=photos_keyboard(),
    )


@router.message(ReportFlow.waiting_photos, F.photo)
async def on_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos: list[dict] = data.get("photos", [])
    if len(photos) >= 2:
        await message.answer("Максимум 2 фото. Нажмите «⏭ Пропустить фото» для продолжения.")
        return
    photo = message.photo[-1]
    photos.append({"filename": "photo.jpg", "file_id": photo.file_id})
    await state.update_data(photos=photos)
    if len(photos) < 2:
        await message.answer(f"Фото {len(photos)}/2 принято. Ещё одно или «⏭ Пропустить фото».")
    else:
        await message.answer("Фото 2/2 принято.")
        await _show_confirmation(message, state)


@router.message(ReportFlow.waiting_photos, F.document)
async def on_photo_file(message: Message, state: FSMContext) -> None:
    if not message.document.mime_type or not message.document.mime_type.startswith("image/"):
        await message.answer("Отправьте изображение.")
        return
    data = await state.get_data()
    photos: list[dict] = data.get("photos", [])
    if len(photos) >= 2:
        await message.answer("Максимум 2 фото. Нажмите «⏭ Пропустить фото» для продолжения.")
        return
    photos.append({"filename": message.document.file_name or "photo.jpg", "file_id": message.document.file_id})
    await state.update_data(photos=photos)
    if len(photos) < 2:
        await message.answer(f"Фото {len(photos)}/2 принято. Ещё одно или «⏭ Пропустить фото».")
    else:
        await message.answer("Фото 2/2 принято.")
        await _show_confirmation(message, state)


@router.message(ReportFlow.waiting_photos, F.text == "⏭ Пропустить фото")
async def photos_skip(message: Message, state: FSMContext) -> None:
    await _show_confirmation(message, state)


@router.callback_query(ReportFlow.confirming, F.data == "confirm:send")
async def confirm_send(callback: CallbackQuery, state: FSMContext, api: ApiClient) -> None:
    data = await state.get_data()
    photos_raw = data.get("photos", [])
    photos = None
    if photos_raw:
        photos = []
        for p in photos_raw:
            tg_file = await callback.bot.get_file(p["file_id"])
            downloaded = await callback.bot.download_file(tg_file.file_path)
            photos.append((p["filename"], downloaded.read()))

    try:
        result = await api.submit_report(
            telegram_id=callback.from_user.id,
            event_type=data["event_type"],
            lat=data["lat"],
            lon=data["lon"],
            event_at=datetime.now(timezone.utc),
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


async def _show_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    lines = [
        f"Тип: {data['event_type_label']}",
        f"Координаты: {data['lat']:.5f}, {data['lon']:.5f}",
    ]
    if photos:
        lines.append(f"Фото: {len(photos)} шт.")

    await state.set_state(ReportFlow.confirming)
    await message.answer(
        "\n".join(lines) + "\n\nВсё верно?",
        reply_markup=confirm_keyboard(),
    )
