from aiogram.dispatcher.filters.state import State, StatesGroup


class LeaveInputState(StatesGroup):
    get_worklog = State()
    get_leave = State()


class WorkLogInputState(StatesGroup):
    confirm_today = State()
    input_date = State()
    input_time = State()
    call_api = State()


class LeaveDayForm(StatesGroup):
    leave_date = State()
    start_time = State()
    end_time = State()


class SingupStates(StatesGroup):
    username = State()
    email = State()
    password = State()
    password2 = State()

