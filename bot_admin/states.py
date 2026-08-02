from aiogram.fsm.state import State, StatesGroup


class AdminFlow(StatesGroup):
    entering_reject_reason = State()
