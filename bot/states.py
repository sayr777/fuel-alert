from aiogram.fsm.state import State, StatesGroup


class ReportFlow(StatesGroup):
    choosing_type = State()
    entering_description = State()  # mandatory, for OTHER type (before location)
    waiting_location = State()
    waiting_photos = State()
    entering_comment = State()      # optional, for all types (after photos)
    confirming = State()