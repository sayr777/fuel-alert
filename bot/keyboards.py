from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

GRADE_LABELS = {
    "AI92": "АИ-92",
    "AI95": "АИ-95",
    "AI98": "АИ-98",
    "AI100": "АИ-100",
    "DT": "ДТ",
    "GAS": "Газ",
}


def event_type_keyboard(event_types: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=et["label_ru"], callback_data=f"etype:{et['code']}")]
        for et in event_types
    ]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def fuel_grades_keyboard(grades: list[str], selected: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for grade in grades:
        mark = "✅ " if grade in selected else ""
        label = GRADE_LABELS.get(grade, grade)
        rows.append([InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"grade:{grade}")])
    rows.append([InlineKeyboardButton(text="✔️ Готово", callback_data="grades:done")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_keyboard(label: str = "Пропустить") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data="skip")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def photos_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустить фото")]],
        resize_keyboard=True,
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm:send")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Сообщить о ситуации")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )