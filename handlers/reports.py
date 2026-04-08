from datetime import date, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import (
    get_user_by_telegram_id, get_period_summary,
    get_category_breakdown, get_transactions_by_period,
)
from keyboards import report_periods, report_detail_button, main_menu
from utils import fmt_summary, fmt_category_breakdown, fmt_amount, fmt_date

router = Router()


def _get_period_dates(period: str) -> tuple[date, date]:
    """Davr nomi bo'yicha sana oralig'ini qaytarish."""
    today = date.today()
    if period == "today":
        return today, today
    elif period == "week":
        return today - timedelta(days=today.weekday()), today
    elif period == "month":
        return today.replace(day=1), today
    return today, today


@router.message(F.text == "📊 Hisobot")
async def show_report_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📊 <b>Qaysi davr uchun hisobot?</b>", reply_markup=report_periods())


@router.callback_query(F.data == "report_today")
async def report_today(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    await _send_summary(callback, session, today, today, period="today")


@router.callback_query(F.data == "report_week")
async def report_week(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    await _send_summary(callback, session, week_start, today, period="week")


@router.callback_query(F.data == "report_month")
async def report_month(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    month_start = today.replace(day=1)
    await _send_summary(callback, session, month_start, today, period="month")


@router.callback_query(F.data == "report_category")
async def report_by_category(callback: types.CallbackQuery, session: AsyncSession):
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    today = date.today()
    month_start = today.replace(day=1)

    from db.models import TransactionType
    rows = await get_category_breakdown(session, user.id, month_start, today, TransactionType.EXPENSE)

    text = fmt_category_breakdown(rows, user.currency)
    await callback.message.edit_text(text)
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()


async def _send_summary(
    callback: types.CallbackQuery,
    session: AsyncSession,
    date_from: date,
    date_to: date,
    period: str = "today",
):
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    summary = await get_period_summary(session, user.id, date_from, date_to)

    # Umumiy xulosa
    text = fmt_summary(summary, user.currency)

    # Top-3 xarajat kategoriyasi
    from db.models import TransactionType
    breakdown = await get_category_breakdown(
        session, user.id, date_from, date_to, TransactionType.EXPENSE
    )
    if breakdown:
        text += "\n\n<b>Top xarajatlar:</b>\n"
        for row in breakdown[:3]:
            amount = fmt_amount(row["total"], user.currency)
            text += f"{row['icon']} {row['category_name']}: {amount} ({row['percent']}%)\n"

    await callback.message.edit_text(text, reply_markup=report_detail_button(period))
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("report_detail_"))
async def report_detail(callback: types.CallbackQuery, session: AsyncSession):
    """Batafsil tranzaksiyalar ro'yxati."""
    period = callback.data.replace("report_detail_", "")
    date_from, date_to = _get_period_dates(period)

    user = await get_user_by_telegram_id(session, callback.from_user.id)
    transactions = await get_transactions_by_period(
        session, user.id, date_from, date_to, limit=20,
    )

    if not transactions:
        await callback.answer("Bu davrda tranzaksiyalar yo'q.", show_alert=True)
        return

    period_labels = {"today": "Bugungi", "week": "Haftalik", "month": "Oylik"}
    label = period_labels.get(period, "")

    lines = [f"📋 <b>{label} tranzaksiyalar:</b>\n"]
    for tx in transactions:
        type_emoji = "💚" if tx.type == "income" else "❤️"
        amount_str = fmt_amount(tx.amount, user.currency)
        cat = f"{tx.category.icon} {tx.category.name}" if tx.category else "📦 Boshqa"
        desc = tx.description or ""
        time_str = tx.created_at.strftime("%d.%m %H:%M")

        lines.append(
            f"{type_emoji} <b>{amount_str}</b> — {cat}\n"
            f"   {f'{desc} · ' if desc else ''}{time_str}"
        )

    text = "\n".join(lines)

    # Xabar uzun bo'lsa 4096 belgidan qisqartiramiz
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>...va yana boshqalar</i>"

    await callback.message.answer(text)
    await callback.answer()
