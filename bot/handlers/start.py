from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from api_client import ApiClient
from keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, api: ApiClient) -> None:
    user = await api.register_user(message.from_user.id)
    await message.answer(
        f"Привет, {user['nickname']}! 👋\n\n"
        "Я помогаю водителям Камчатки делиться информацией о топливе на АЗС.\n\n"
        "Нажмите «📢 Сообщить о ситуации», чтобы отправить отчёт.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
@router.message(lambda m: m.text == "ℹ️ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Как пользоваться ботом:\n\n"
        "1. Нажмите «📢 Сообщить о ситуации»\n"
        "2. Выберите тип события\n"
        "3. Заполните детали (марка топлива, цена и т.д.)\n"
        "4. Отправьте геолокацию АЗС\n"
        "5. При желании прикрепите фото (как файл — так сохранится EXIF)\n"
        "6. Подтвердите отправку\n\n"
        "Отчёты появляются на карте после проверки (если требуется модерация)."
    )