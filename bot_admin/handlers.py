import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import get_settings
from states import AdminFlow

router = Router()
settings = get_settings()


@router.callback_query(F.data.startswith("mod:approve:"))
async def on_approve(callback: CallbackQuery) -> None:
    report_id = int(callback.data.split(":")[2])
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.api_base_url}/moderation/{report_id}/publish",
            json={"moderator_id": "admin_bot"},
            headers={"Authorization": f"Bearer {settings.moderator_token}"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            ok = resp.status < 300

    if callback.message:
        new_text = (callback.message.text or "") + "\n\n✅ Одобрено"
        await callback.message.edit_text(new_text)
    await callback.answer("✅ Репорт одобрен" if ok else "Ошибка при одобрении")


@router.callback_query(F.data.startswith("mod:reject:"))
async def on_reject(callback: CallbackQuery, state: FSMContext) -> None:
    report_id = int(callback.data.split(":")[2])
    message_id = callback.message.message_id if callback.message else None
    await state.set_state(AdminFlow.entering_reject_reason)
    await state.update_data(report_id=report_id, message_id=message_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите причину отклонения:")


@router.message(AdminFlow.entering_reject_reason, F.text)
async def on_reject_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    report_id: int = data["report_id"]
    reason: str = message.text or ""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.api_base_url}/moderation/{report_id}/reject",
            json={"moderator_id": "admin_bot", "reason": reason},
            headers={"Authorization": f"Bearer {settings.moderator_token}"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            ok = resp.status < 300

    await state.clear()
    if ok:
        await message.answer(f"❌ Репорт #{report_id} отклонён. Причина: {reason}")
    else:
        await message.answer(f"Ошибка при отклонении репорта #{report_id}.")
