from aiogram.dispatcher.filters.state import State, StatesGroup


class Form_state(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()


class ReqPict(StatesGroup):
    paypal = State()
    iban = State()


class Holded(StatesGroup):
    paypal = State()
    iban = State()


class ChangeState(StatesGroup):
    wallet = State()
    paytag = State()


class AdminState(StatesGroup):
    answer_query = State()
    answer_iban = State()
    summ = State()


class MentorState(StatesGroup):
    label = State()
    info = State()