from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def moderation_keyboard(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{report_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{report_id}"),
    ]])
