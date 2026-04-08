from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from keyboards import main_menu

router = Router()


@router.message()
async def unknown_message(message: types.Message, state: FSMContext):
    """Noma'lum xabar — foydalanuvchini yo'naltirish."""
    current_state = await state.get_state()
    if current_state:
        return  # FSM state da boshqa handler ishlayapti

    await message.answer(
        "❓ Tushunmadim.\n\n"
        "Kirim yoki chiqimni yozish uchun:\n"
        "• Tugmani bosing 👇\n"
        "• Yoki erkin yozing: <code>50 ming non uchun</code>\n"
        "• Yoki ovozli xabar yuboring 🎙",
        reply_markup=main_menu(),
    )
