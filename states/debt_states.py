from aiogram.fsm.state import State, StatesGroup


class DebtState(StatesGroup):
    waiting_type = State()        # lent / borrowed
    waiting_person = State()      # kiming ismi
    waiting_amount = State()      # summa
    waiting_due_date = State()    # muddat (ixtiyoriy)
    waiting_partial_amount = State()  # qisman to'lash summasi
