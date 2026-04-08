from decimal import Decimal
from datetime import date

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import (
    get_user_by_telegram_id, add_debt, get_user_debts,
    mark_debt_paid, pay_debt_partial, get_debts_summary,
)
from db.models.debt import DebtType
from keyboards import main_menu, debt_actions
from keyboards.inline import InlineKeyboardBuilder, InlineKeyboardButton
from states import DebtState
from utils import fmt_debt, fmt_amount

router = Router()


@router.message(F.text == "💳 Qarzlar")
async def show_debts_menu(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    debts = await get_user_debts(session, user.id)
    summary = await get_debts_summary(session, user.id)

    if not debts:
        await message.answer(
            "📭 Hozircha qarzlar yo'q.\n\nYangi qarz qo'shish:",
            reply_markup=_add_debt_keyboard(),
        )
        return

    lent = fmt_amount(summary["total_lent"], user.currency)
    borrowed = fmt_amount(summary["total_borrowed"], user.currency)

    header = (
        f"💳 <b>Qarzlar</b>\n\n"
        f"📤 Berganlarim: <b>{lent}</b> ({summary['lent_count']} ta)\n"
        f"📥 Olganlarim: <b>{borrowed}</b> ({summary['borrowed_count']} ta)\n"
        f"{'─' * 22}\n\n"
    )

    await message.answer(header + "Qarz tanlang:")

    for debt in debts[:10]:  # Ko'p bo'lsa 10 ta ko'rsatamiz
        await message.answer(
            fmt_debt(debt, user.currency),
            reply_markup=debt_actions(debt.id),
        )

    await message.answer("➕ Yangi qarz:", reply_markup=_add_debt_keyboard())


def _add_debt_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📤 Men berdim", callback_data="debt_add_lent"),
        InlineKeyboardButton(text="📥 Men oldim", callback_data="debt_add_borrowed"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="debt_back"))
    return builder.as_markup()


# --- Qarz qo'shish FSM ---

@router.callback_query(F.data.in_({"debt_add_lent", "debt_add_borrowed"}))
async def start_add_debt(callback: types.CallbackQuery, state: FSMContext):
    debt_type = "lent" if callback.data == "debt_add_lent" else "borrowed"
    await state.set_state(DebtState.waiting_person)
    await state.update_data(debt_type=debt_type)

    type_text = "bergansiz" if debt_type == "lent" else "olgansiz"
    await callback.message.edit_text(
        f"👤 Kim{'dan' if debt_type == 'borrowed' else 'ga'} qarz {type_text}?\n\n"
        f"Ismini yozing:"
    )
    await callback.answer()


@router.message(DebtState.waiting_person)
async def debt_person(message: types.Message, state: FSMContext):
    await state.update_data(person_name=message.text.strip())
    await state.set_state(DebtState.waiting_amount)
    await message.answer("💰 Qancha miqdorda? (raqam kiriting):")


@router.message(DebtState.waiting_amount)
async def debt_amount(message: types.Message, state: FSMContext):
    try:
        # "500 ming", "1.5 mln", oddiy raqam
        text = message.text.lower().replace(" ", "")
        if "mln" in text or "million" in text:
            amount = float(text.replace("mln", "").replace("million", "")) * 1_000_000
        elif "ming" in text or "k" in text:
            amount = float(text.replace("ming", "").replace("k", "")) * 1_000
        else:
            amount = float(text.replace(",", "."))

        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri summa. Masalan: <code>500000</code> yoki <code>500 ming</code>")
        return

    await state.update_data(amount=amount)
    await state.set_state(DebtState.waiting_due_date)
    await message.answer(
        "📅 Qaytarish muddati? (ixtiyoriy)\n\n"
        "Format: <code>15.04.2026</code>\n"
        "Muddat yo'q bo'lsa — <code>-</code> yozing"
    )


@router.message(DebtState.waiting_due_date)
async def debt_due_date(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    due_date = None
    if message.text.strip() != "-":
        try:
            due_date = date.fromisoformat(
                message.text.strip().replace(".", "-")
            )
        except ValueError:
            await message.answer("❌ Sana formati noto'g'ri. Masalan: <code>15.04.2026</code>")
            return

    user = await get_user_by_telegram_id(session, message.from_user.id)

    debt = await add_debt(
        session=session,
        user_id=user.id,
        type=DebtType(data["debt_type"]),
        person_name=data["person_name"],
        amount=Decimal(str(data["amount"])),
        due_date=due_date,
    )

    type_emoji = "📤" if debt.type == DebtType.LENT else "📥"
    amount_str = fmt_amount(debt.amount, user.currency)

    await message.answer(
        f"✅ Qarz saqlandi!\n\n"
        f"{type_emoji} <b>{debt.person_name}</b> — {amount_str}",
        reply_markup=main_menu(),
    )


# --- Qarz to'lash ---

@router.callback_query(F.data.startswith("debt_paid_"))
async def debt_paid(callback: types.CallbackQuery, session: AsyncSession):
    debt_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    success = await mark_debt_paid(session, debt_id, user.id)

    if success:
        await callback.message.edit_text("✅ Qarz to'liq yopildi!")
    else:
        await callback.answer("❌ Xatolik.", show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith("debt_partial_"))
async def debt_partial_start(callback: types.CallbackQuery, state: FSMContext):
    debt_id = int(callback.data.split("_")[2])
    await state.set_state(DebtState.waiting_partial_amount)
    await state.update_data(debt_id=debt_id)
    await callback.message.answer("💰 Necha so'm to'landi? Miqdorni kiriting:")
    await callback.answer()


@router.message(DebtState.waiting_partial_amount)
async def debt_partial_pay(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    try:
        amount = Decimal(message.text.replace(" ", "").replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (ValueError, Exception):
        await message.answer("❌ Noto'g'ri summa.", reply_markup=main_menu())
        return

    user = await get_user_by_telegram_id(session, message.from_user.id)
    debt = await pay_debt_partial(session, data["debt_id"], user.id, amount)

    if debt:
        amount_str = fmt_amount(amount, user.currency)
        remaining_str = fmt_amount(debt.remaining_amount, user.currency)
        status = "✅ To'liq yopildi!" if debt.is_paid else f"Qolgan: {remaining_str}"
        await message.answer(f"💰 {amount_str} to'landi. {status}", reply_markup=main_menu())
    else:
        await message.answer("❌ Xatolik.", reply_markup=main_menu())


@router.callback_query(F.data == "debt_back")
async def debt_back(callback: types.CallbackQuery):
    await callback.message.edit_text("Bosh menyu.")
    await callback.message.answer("👇", reply_markup=main_menu())
    await callback.answer()
