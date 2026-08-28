from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    waiting_review_url = State()
    waiting_review_screenshot = State()