from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import get_user_by_telegram_id, update_user_language, update_user_currency
from db.models.user import Language, Currency
from keyboards import settings_menu, languages, currencies, main_menu

router = Router()


@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)

    lang_display = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}.get(user.language, "—")
    curr_display = user.currency if isinstance(user.currency, str) else user.currency.value

    await message.answer(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🌐 Til: {lang_display}\n"
        f"💱 Valyuta: {curr_display}\n",
        reply_markup=settings_menu(),
    )


@router.callback_query(F.data == "settings_lang")
async def choose_language(callback: types.CallbackQuery):
    await callback.message.edit_text("🌐 Tilni tanlang:", reply_markup=languages())
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery, session: AsyncSession):
    lang_code = callback.data.split("_")[1]
    try:
        lang = Language(lang_code)
    except ValueError:
        await callback.answer("❌ Noma'lum til.", show_alert=True)
        return

    await update_user_language(session, callback.from_user.id, lang)
    labels = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}
    await callback.message.edit_text(f"✅ Til o'zgartirildi: {labels.get(lang_code, lang_code)}")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "settings_currency")
async def choose_currency(callback: types.CallbackQuery):
    await callback.message.edit_text("💱 Valyutani tanlang:", reply_markup=currencies())
    await callback.answer()


@router.callback_query(F.data.startswith("curr_"))
async def set_currency(callback: types.CallbackQuery, session: AsyncSession):
    curr_code = callback.data.split("_")[1]
    try:
        currency = Currency(curr_code)
    except ValueError:
        await callback.answer("❌ Noma'lum valyuta.", show_alert=True)
        return

    await update_user_currency(session, callback.from_user.id, currency)
    await callback.message.edit_text(f"✅ Valyuta o'zgartirildi: {curr_code}")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "settings_reports")
async def settings_reports(callback: types.CallbackQuery, session: AsyncSession):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    from db.queries import update_user_report_settings

    user = await get_user_by_telegram_id(session, callback.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"📅 Kunlik {'✅' if user.daily_report else '❌'}",
            callback_data="toggle_daily"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📆 Haftalik {'✅' if user.weekly_report else '❌'}",
            callback_data="toggle_weekly"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🗓 Oylik {'✅' if user.monthly_report else '❌'}",
            callback_data="toggle_monthly"
        )
    )
    await callback.message.edit_text("🔔 Avtomatik hisobotlar:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_report(callback: types.CallbackQuery, session: AsyncSession):
    from db.queries import update_user_report_settings
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    key = callback.data.replace("toggle_", "")

    kwargs = {}
    if key == "daily":
        kwargs["daily_report"] = not user.daily_report
    elif key == "weekly":
        kwargs["weekly_report"] = not user.weekly_report
    elif key == "monthly":
        kwargs["monthly_report"] = not user.monthly_report

    await update_user_report_settings(session, callback.from_user.id, **kwargs)
    await settings_reports(callback, session)
