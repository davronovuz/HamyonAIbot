"""
Tranzaksiya handleri.
Foydalanuvchi matn yoki ovoz yuboradi → AI parse → tasdiqlash → DB saqlash.
Kirim/Chiqim tugmalari bosilganda ham shu handler ishlaydi.
"""
import io
import logging
from decimal import Decimal

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import (
    get_user_by_telegram_id, add_transaction,
    get_user_categories, get_category_by_name,
)
from db.models import TransactionType, InputSource
from keyboards import main_menu, confirm_transaction, select_category
from services import parse_transaction_text, process_voice_message
from states import TransactionState
from utils import fmt_amount

logger = logging.getLogger(__name__)
router = Router()

# Tugmalar matni
INCOME_BTN = "➕ Kirim"
EXPENSE_BTN = "➖ Chiqim"


@router.message(F.text == INCOME_BTN)
async def btn_income(message: types.Message, state: FSMContext):
    await state.set_state(TransactionState.waiting_amount)
    await state.update_data(forced_type="income")
    await message.answer(
        "💚 <b>Kirim miqdorini kiriting:</b>\n\n"
        "Masalan: <code>500000</code> yoki <code>500 ming maosh</code>",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(F.text == EXPENSE_BTN)
async def btn_expense(message: types.Message, state: FSMContext):
    await state.set_state(TransactionState.waiting_amount)
    await state.update_data(forced_type="expense")
    await message.answer(
        "❤️ <b>Chiqim miqdorini kiriting:</b>\n\n"
        "Masalan: <code>50000</code> yoki <code>50 ming non uchun</code>",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(TransactionState.waiting_amount)
async def handle_manual_amount(message: types.Message, state: FSMContext, session: AsyncSession):
    """Kirim/Chiqim tugmasi bosilgandan keyin matn kiritildi."""
    data = await state.get_data()
    forced_type = data.get("forced_type", "expense")
    await _process_text(message, state, session, text=message.text, forced_type=forced_type)


@router.message(F.voice)
async def handle_voice(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Ovozli xabar — Whisper → GPT → tasdiqlash."""
    await state.clear()
    processing_msg = await message.answer("🎙 Ovoz qayta ishlanmoqda...")

    try:
        file = await bot.get_file(message.voice.file_id)
        voice_bytes = io.BytesIO()
        await bot.download_file(file.file_path, destination=voice_bytes)
        voice_bytes.seek(0)

        text, parsed = await process_voice_message(voice_bytes.read())
        await processing_msg.delete()

        if not text:
            await message.answer("❌ Ovozni tushunmadim. Qayta urinib ko'ring.", reply_markup=main_menu())
            return

        await message.answer(f"🎙 Eshitildi: <i>«{text}»</i>")

        if not parsed or parsed.amount <= 0:
            await message.answer(
                "🤔 Summani aniqlay olmadim. Qo'lda kiriting:",
                reply_markup=main_menu(),
            )
            return

        await _show_confirmation(message, state, session, parsed.type, parsed.amount,
                                  parsed.category, parsed.description,
                                  voice_text=text, source=InputSource.VOICE,
                                  confidence=parsed.confidence)

    except Exception as e:
        logger.error(f"Voice handler xatoligi: {e}")
        await processing_msg.delete()
        await message.answer("❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.", reply_markup=main_menu())


@router.message(
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_({"➕ Kirim", "➖ Chiqim", "📋 Tarix", "📊 Hisobot", "💳 Qarzlar", "⚙️ Sozlamalar", "📱 Mini App"}),
)
async def handle_free_text(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Foydalanuvchi erkin matn yozdi (tugma bosmay).
    AI parse qilishga urinadi.
    """
    current_state = await state.get_state()
    if current_state:
        return  # Boshqa state da ishlayapti, u handlerga topshiramiz

    await _process_text(message, state, session, text=message.text)


async def _process_text(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    text: str,
    forced_type: str | None = None,
):
    """Matnni parse qilish va tasdiqlashga yuborish."""
    parsed = await parse_transaction_text(text)

    if not parsed or parsed.amount <= 0:
        await message.answer(
            "🤔 Summani tushunmadim.\n\n"
            "Masalan: <code>50 ming non uchun</code> yoki <code>500000 maosh</code>",
            reply_markup=main_menu(),
        )
        await state.clear()
        return

    tx_type = forced_type or parsed.type
    await _show_confirmation(
        message, state, session,
        tx_type, parsed.amount, parsed.category, parsed.description,
        source=InputSource.TEXT, confidence=parsed.confidence,
    )


async def _show_confirmation(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    tx_type: str,
    amount: float,
    category_name: str,
    description: str,
    voice_text: str | None = None,
    source: InputSource = InputSource.TEXT,
    confidence: float = 1.0,
):
    """Tasdiqlash xabarini ko'rsatish."""
    user = await get_user_by_telegram_id(session, message.from_user.id)
    currency = user.currency if user else None

    type_emoji = "💚" if tx_type == "income" else "❤️"
    type_text = "Kirim" if tx_type == "income" else "Chiqim"
    amount_str = fmt_amount(Decimal(str(amount)), currency)

    # Kategoriyani DB dan topish
    category = await get_category_by_name(session, user.id, category_name)
    cat_display = f"{category.icon} {category.name}" if category else f"📦 {category_name}"

    text = (
        f"{type_emoji} <b>{type_text}</b>\n\n"
        f"💰 Summa: <b>{amount_str}</b>\n"
        f"📁 Kategoriya: {cat_display}\n"
        f"📝 Tavsif: {description}\n\n"
        f"✅ To'g'rimi?"
    )

    await state.set_state(TransactionState.confirming)
    await state.update_data(
        tx_type=tx_type,
        amount=amount,
        category_id=category.id if category else None,
        category_name=category_name,
        description=description,
        voice_text=voice_text,
        source=source.value,
        confidence=confidence,
    )

    # Kategoriya noaniq bo'lsa (past confidence) — boshqa kategoriya tanlash imkoni
    if confidence < 0.7 and not category:
        categories = await get_user_categories(
            session, user.id,
            type_filter=TransactionType(tx_type)
        )
        await message.answer(
            text + "\n\n<i>Kategoriyani aniq topamadim, tanlang:</i>",
            reply_markup=select_category(categories[:10], tx_type),
        )
    else:
        await message.answer(text, reply_markup=confirm_transaction(tx_type, amount, category_name, description))


@router.callback_query(TransactionState.confirming, F.data == "tx_confirm")
async def confirm_tx(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Foydalanuvchi tasdiqladi — DB ga saqlash."""
    data = await state.get_data()
    await state.clear()

    user = await get_user_by_telegram_id(session, callback.from_user.id)

    tx = await add_transaction(
        session=session,
        user_id=user.id,
        type=TransactionType(data["tx_type"]),
        amount=Decimal(str(data["amount"])),
        category_id=data.get("category_id"),
        description=data.get("description"),
        voice_text=data.get("voice_text"),
        source=InputSource(data.get("source", "text")),
    )

    type_emoji = "💚" if data["tx_type"] == "income" else "❤️"
    amount_str = fmt_amount(Decimal(str(data["amount"])), user.currency)

    await callback.message.edit_text(
        f"{type_emoji} Saqlandi!\n\n"
        f"💰 {amount_str} — {data.get('description', '')}"
    )
    await callback.message.answer("✅", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(TransactionState.confirming, F.data == "tx_cancel")
async def cancel_tx(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def select_category_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Foydalanuvchi kategoriya tanladi."""
    parts = callback.data.split("_")
    category_id = int(parts[1])

    data = await state.get_data()
    await state.update_data(category_id=category_id)

    # Tasdiqlash xabariga qaytish
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    data = await state.get_data()

    type_emoji = "💚" if data["tx_type"] == "income" else "❤️"
    type_text = "Kirim" if data["tx_type"] == "income" else "Chiqim"
    amount_str = fmt_amount(Decimal(str(data["amount"])), user.currency)

    await state.set_state(TransactionState.confirming)
    await callback.message.edit_text(
        f"{type_emoji} <b>{type_text}</b>\n\n"
        f"💰 Summa: <b>{amount_str}</b>\n"
        f"📝 Tavsif: {data.get('description', '')}\n\n"
        f"✅ To'g'rimi?",
        reply_markup=confirm_transaction(
            data["tx_type"], data["amount"], data.get("category_name", ""), data.get("description", "")
        ),
    )
    await callback.answer()
