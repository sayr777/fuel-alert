from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import get_settings
from keyboards import main_menu_keyboard
from states import FeedbackFlow

router = Router()
settings = get_settings()


@router.message(F.text == "💡 Пожелание")
async def start_feedback(message: Message, state: FSMContext) -> None:
    await state.set_state(FeedbackFlow.entering_feedback)
    await message.answer("Напишите ваше пожелание или предложение по улучшению сервиса:")


@router.message(FeedbackFlow.entering_feedback, F.text)
async def on_feedback(message: Message, state: FSMContext) -> None:
    if settings.admin_chat_id:
        username = message.from_user.username
        sender = f"@{username}" if username else f"id:{message.from_user.id}"
        text = f"💡 Пожелание от {sender}:\n\n{message.text}"
        if settings.admin_bot_token:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"https://api.telegram.org/bot{settings.admin_bot_token}/sendMessage",
                    json={"chat_id": settings.admin_chat_id, "text": text},
                )
        else:
            await message.bot.send_message(settings.admin_chat_id, text)
    await state.clear()
    await message.answer("Спасибо за пожелание! Мы обязательно его рассмотрим. 🙏", reply_markup=main_menu_keyboard())


@router.message(FeedbackFlow.entering_feedback)
async def on_feedback_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, напишите пожелание текстом.")
