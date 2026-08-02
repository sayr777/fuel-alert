from vkbottle import Keyboard, Text, Callback, KeyboardButtonColor

GRADE_LABELS = {
    "AI92": "АИ-92",
    "AI95": "АИ-95",
    "AI98": "АИ-98",
    "AI100": "АИ-100",
    "DT": "ДТ",
    "GAS": "Газ",
}


def main_menu_keyboard() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📢 Сообщить о ситуации"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("💡 Пожелание"))
    kb.row()
    kb.add(Text("ℹ️ Помощь"))
    return kb.get_json()


def event_type_keyboard(event_types: list[dict]) -> str:
    kb = Keyboard(inline=True)
    for et in event_types:
        kb.add(Callback(et["label_ru"][:40], payload={"action": "etype", "code": et["code"]}))
        kb.row()
    kb.add(Callback("✏️ Другое", payload={"action": "etype", "code": "OTHER"}))
    kb.row()
    kb.add(Callback("❌ Отмена", payload={"action": "cancel"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()


def fuel_grades_keyboard(grades: list[str], selected: set[str]) -> str:
    kb = Keyboard(inline=True)
    for grade in grades:
        mark = "✅ " if grade in selected else ""
        kb.add(Callback(f"{mark}{GRADE_LABELS.get(grade, grade)}", payload={"action": "grade", "code": grade}))
        kb.row()
    kb.add(Callback("✔️ Готово", payload={"action": "grades_done"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback("❌ Отмена", payload={"action": "cancel"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()


def location_keyboard() -> str:
    kb = Keyboard(inline=False, one_time=True)
    kb.add(Text("📍 Пропустить геолокацию"))
    return kb.get_json()


def skip_photos_keyboard() -> str:
    kb = Keyboard(inline=False, one_time=True)
    kb.add(Text("⏭ Пропустить фото"))
    return kb.get_json()


def skip_comment_keyboard() -> str:
    kb = Keyboard(inline=False, one_time=True)
    kb.add(Text("⏭ Без комментария"))
    return kb.get_json()


def confirm_keyboard() -> str:
    kb = Keyboard(inline=True)
    kb.add(Callback("✅ Отправить", payload={"action": "confirm"}), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback("❌ Отмена", payload={"action": "cancel"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()
