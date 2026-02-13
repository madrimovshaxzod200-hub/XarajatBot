from aiogram.fsm.state import State, StatesGroup


class ExpenseState(StatesGroup):
    amount = State()
    category = State()


class ReminderState(StatesGroup):
    time = State()
