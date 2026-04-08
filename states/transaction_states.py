from aiogram.fsm.state import State, StatesGroup


class TransactionState(StatesGroup):
    # AI kategoriyani aniqlay olmagan holatda foydalanuvchidan so'rash
    waiting_category = State()

    # Qo'lda kiritish: faqat summa so'rash (matn tavsif sifatida ishlatiladi)
    waiting_amount = State()

    # Tranzaksiyani tasdiqlab turish (ma'lumotlar FSM data da saqlanadi)
    confirming = State()
