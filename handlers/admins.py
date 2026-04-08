from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from data.config import ADMINS
from db.models import User, Transaction

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


@router.message(Command("stats"))
async def admin_stats(message: types.Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    user_count = await session.scalar(select(func.count(User.id)))
    tx_count = await session.scalar(select(func.count(Transaction.id)))

    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{user_count}</b>\n"
        f"💳 Tranzaksiyalar: <b>{tx_count}</b>"
    )
