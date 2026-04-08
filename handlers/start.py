from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import get_or_create_user
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()

    user, is_new = await get_or_create_user(
        session=session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if is_new:
        await message.answer(
            f"Assalomu alaykum, <b>{message.from_user.first_name}</b>! 👋\n\n"
            f"<b>HamyonAI</b> botiga xush kelibsiz!\n\n"
            f"Bu bot sizga:\n"
            f"✅ Kirim va chiqimlarni kuzatish\n"
            f"✅ Ovozli xabar orqali tez kiritish\n"
            f"✅ Kunlik, haftalik, oylik hisobotlar\n"
            f"✅ Qarzlarni boshqarish\n\n"
            f"Boshlash uchun pastdagi tugmalardan foydalaning 👇",
            reply_markup=main_menu(),
        )
    else:
        await message.answer(
            f"Xush kelibsiz, <b>{message.from_user.first_name}</b>! 👋",
            reply_markup=main_menu(),
        )
