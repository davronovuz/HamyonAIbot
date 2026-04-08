from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import Category


def confirm_transaction(tx_type: str, amount: float, category: str, desc: str) -> InlineKeyboardMarkup:
    """Tranzaksiyani tasdiqlash."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tx_confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="tx_cancel"),
    )
    return builder.as_markup()


def report_periods() -> InlineKeyboardMarkup:
    """Hisobot davri tanlash."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Bugun", callback_data="report_today"),
        InlineKeyboardButton(text="📆 Hafta", callback_data="report_week"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Oy", callback_data="report_month"),
        InlineKeyboardButton(text="📈 Kategoriya", callback_data="report_category"),
    )
    return builder.as_markup()


def report_detail_button(period: str) -> InlineKeyboardMarkup:
    """Hisobot ostiga 'Batafsil' tugmasi."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Batafsil ro'yxat", callback_data=f"report_detail_{period}"),
    )
    return builder.as_markup()


def debt_actions(debt_id: int) -> InlineKeyboardMarkup:
    """Qarz uchun amallar."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ To'landi", callback_data=f"debt_paid_{debt_id}"),
        InlineKeyboardButton(text="💰 Qisman", callback_data=f"debt_partial_{debt_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"debt_delete_{debt_id}"),
    )
    return builder.as_markup()


def select_category(categories: list[Category], tx_type: str) -> InlineKeyboardMarkup:
    """Kategoriya tanlash (AI aniqlay olmagan holatda)."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.icon} {cat.name}",
            callback_data=f"cat_{cat.id}_{tx_type}",
        )
    builder.adjust(2)
    return builder.as_markup()


def settings_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 Til", callback_data="settings_lang"),
        InlineKeyboardButton(text="💱 Valyuta", callback_data="settings_currency"),
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Hisobotlar", callback_data="settings_reports"),
    )
    return builder.as_markup()


def languages() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
    )
    return builder.as_markup()


def currencies() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 UZS (so'm)", callback_data="curr_UZS"),
        InlineKeyboardButton(text="🇺🇸 USD ($)", callback_data="curr_USD"),
    )
    builder.row(
        InlineKeyboardButton(text="🇷🇺 RUB (₽)", callback_data="curr_RUB"),
        InlineKeyboardButton(text="🇪🇺 EUR (€)", callback_data="curr_EUR"),
    )
    return builder.as_markup()
