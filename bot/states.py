from aiogram.fsm.state import State, StatesGroup


class ReportFlow(StatesGroup):
    choosing_type = State()
    choosing_grades = State()
    entering_price = State()
    entering_limit = State()
    entering_wait = State()
    entering_pump = State()
    entering_reason = State()
    entering_link = State()
    entering_description = State()
    waiting_location = State()
    waiting_photos = State()
    confirming = State()