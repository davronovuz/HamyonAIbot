from datetime import date, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import get_user_by_telegram_id, get_period_summary, get_category_breakdown
from keyboards import report_periods, main_menu
from utils import fmt_summary, fmt_category_breakdown

router = Router()


@router.message(F.text == "📊 Hisobot")
async def show_report_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📊 <b>Qaysi davr uchun hisobot?</b>", reply_markup=report_periods())


@router.callback_query(F.data == "report_today")
async def report_today(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    await _send_summary(callback, session, today, today)


@router.callback_query(F.data == "report_week")
async def report_week(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    await _send_summary(callback, session, week_start, today)


@router.callback_query(F.data == "report_month")
async def report_month(callback: types.CallbackQuery, session: AsyncSession):
    today = date.today()
    month_start = today.replace(day=1)
    await _send_summary(callback, session, month_start, today)


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


async def _send_summary(callback: types.CallbackQuery, session: AsyncSession, date_from: date, date_to: date):
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    summary = await get_period_summary(session, user.id, date_from, date_to)
    text = fmt_summary(summary, user.currency)
    await callback.message.edit_text(text)
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()
