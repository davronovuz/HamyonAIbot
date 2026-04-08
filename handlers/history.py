"""
Tarix handleri — so'nggi tranzaksiyalar ro'yxati.
Har bir yozuv: kategoriya icon, summa, tavsif, sana/vaqt.
Pagination va o'chirish imkoniyati bilan.
"""
from datetime import date, timedelta
from decimal import Decimal

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import (
    get_user_by_telegram_id,
    get_transactions_by_period,
    delete_transaction,
)
from keyboards import main_menu
from utils import fmt_amount, fmt_date

router = Router()

PAGE_SIZE = 5


def _fmt_transaction_line(tx, currency) -> str:
    """Bitta tranzaksiyani batafsil formatlash."""
    type_emoji = "💚" if tx.type == "income" else "❤️"
    amount_str = fmt_amount(tx.amount, currency)

    cat_str = ""
    if tx.category:
        cat_str = f"{tx.category.icon} {tx.category.name}"
    else:
        cat_str = "📦 Boshqa"

    desc = tx.description or ""
    time_str = tx.created_at.strftime("%H:%M")
    date_str = fmt_date(tx.created_at)

    return (
        f"{type_emoji} <b>{amount_str}</b>\n"
        f"   {cat_str}\n"
        f"   {f'📝 {desc}' if desc else ''}\n"
        f"   🕐 {date_str}, {time_str}"
    ).strip()


def _history_keyboard(page: int, total: int) -> InlineKeyboardBuilder:
    """Pagination tugmalari."""
    builder = InlineKeyboardBuilder()
    buttons = []

    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"history_page_{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"history_page_{page + 1}"))

    if buttons:
        builder.row(*buttons)

    return builder


@router.message(F.text == "📋 Tarix")
async def show_history(message: types.Message, state: FSMContext, session: AsyncSession):
    """So'nggi tranzaksiyalar ro'yxati."""
    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)

    # So'nggi 90 kun ichidagi tranzaksiyalar
    date_to = date.today()
    date_from = date_to - timedelta(days=90)

    transactions = await get_transactions_by_period(
        session, user.id, date_from, date_to, limit=100
    )

    if not transactions:
        await message.answer(
            "📭 Hozircha tranzaksiyalar yo'q.\n\n"
            "Kirim yoki chiqim qo'shish uchun pastdagi tugmalardan foydalaning.",
            reply_markup=main_menu(),
        )
        return

    await _send_history_page(message, transactions, user.currency, page=0)


async def _send_history_page(
    message: types.Message,
    transactions: list,
    currency,
    page: int,
    edit: bool = False,
):
    """Berilgan sahifadagi tranzaksiyalarni ko'rsatish."""
    total = len(transactions)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_txs = transactions[start:end]

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    lines = [f"📋 <b>Tranzaksiyalar tarixi</b> ({page + 1}/{total_pages})\n"]

    for tx in page_txs:
        lines.append(_fmt_transaction_line(tx, currency))
        lines.append("")  # Bo'sh qator

    text = "\n".join(lines)

    # Pagination + har bir tranzaksiya uchun o'chirish tugmasi
    builder = InlineKeyboardBuilder()

    for tx in page_txs:
        type_label = "kirim" if tx.type == "income" else "chiqim"
        short_amount = fmt_amount(tx.amount, currency)
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {short_amount} — {tx.description or type_label}",
                callback_data=f"txdel_{tx.id}",
            )
        )

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"history_page_{page}_{page - 1}"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"history_page_{page}_{page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    markup = builder.as_markup()

    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("history_page_"))
async def history_pagination(callback: types.CallbackQuery, session: AsyncSession):
    """Sahifalar orasida ko'chish."""
    parts = callback.data.split("_")
    new_page = int(parts[-1])

    user = await get_user_by_telegram_id(session, callback.from_user.id)

    date_to = date.today()
    date_from = date_to - timedelta(days=90)
    transactions = await get_transactions_by_period(
        session, user.id, date_from, date_to, limit=100
    )

    await _send_history_page(callback.message, transactions, user.currency, page=new_page, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("txdel_"))
async def confirm_delete_tx(callback: types.CallbackQuery):
    """O'chirishni tasdiqlash."""
    tx_id = int(callback.data.split("_")[1])

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"txdel_yes_{tx_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="txdel_no"),
    )
    await callback.message.edit_text(
        f"🗑 #{tx_id} tranzaksiyani o'chirmoqchimisiz?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("txdel_yes_"))
async def do_delete_tx(callback: types.CallbackQuery, session: AsyncSession):
    """Tranzaksiyani o'chirish."""
    tx_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(session, callback.from_user.id)

    success = await delete_transaction(session, tx_id, user.id)
    if success:
        await callback.message.edit_text("✅ Tranzaksiya o'chirildi.")
    else:
        await callback.message.edit_text("❌ O'chirishda xatolik.")
    await callback.message.answer("👇", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "txdel_no")
async def cancel_delete_tx(callback: types.CallbackQuery):
    """O'chirishni bekor qilish."""
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("👇", reply_markup=main_menu())
    await callback.answer()
