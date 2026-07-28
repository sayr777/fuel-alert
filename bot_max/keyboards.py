from typing import Any

GRADE_LABELS = {
    "AI92": "АИ-92",
    "AI95": "АИ-95",
    "AI98": "АИ-98",
    "AI100": "АИ-100",
    "DT": "ДТ",
    "GAS": "Газ",
}


def _cb(text: str, payload: str) -> dict[str, Any]:
    return {"type": "callback", "text": text, "payload": payload}


def _geo(text: str) -> dict[str, Any]:
    return {"type": "request_geo_location", "text": text}


def main_menu() -> list[list[dict]]:
    return [
        [_cb("📢 Сообщить о ситуации", "start_report")],
        [_cb("ℹ️ Помощь", "help")],
    ]


def event_type_keyboard(event_types: list[dict]) -> list[list[dict]]:
    buttons: list[list[dict]] = []
    row: list[dict] = []
    for et in event_types:
        row.append(_cb(et["label_ru"], f"etype:{et['code']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([_cb("❌ Отмена", "cancel")])
    return buttons


def fuel_grades_keyboard(grades: list[str], selected: set[str]) -> list[list[dict]]:
    buttons: list[list[dict]] = []
    row: list[dict] = []
    for grade in grades:
        label = GRADE_LABELS.get(grade, grade)
        if grade in selected:
            label = f"✅ {label}"
        row.append(_cb(label, f"grade:{grade}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([_cb("✔ Готово", "grades_done"), _cb("❌ Отмена", "cancel")])
    return buttons


def location_keyboard() -> list[list[dict]]:
    return [
        [_geo("📍 Отправить геолокацию")],
        [_cb("❌ Отмена", "cancel")],
    ]


def photos_keyboard() -> list[list[dict]]:
    return [
        [_cb("⏭ Пропустить фото", "skip_photo")],
        [_cb("❌ Отмена", "cancel")],
    ]


def comment_keyboard() -> list[list[dict]]:
    return [
        [_cb("⏭ Без комментария", "skip_comment")],
        [_cb("❌ Отмена", "cancel")],
    ]


def confirm_keyboard() -> list[list[dict]]:
    return [
        [_cb("✅ Отправить", "confirm_send"), _cb("❌ Отмена", "cancel")],
    ]
