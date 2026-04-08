from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo,
)
from data.config import WEBAPP_URL


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="➕ Kirim"), KeyboardButton(text="➖ Chiqim")],
        [KeyboardButton(text="📋 Tarix"), KeyboardButton(text="📊 Hisobot")],
        [KeyboardButton(text="💳 Qarzlar"), KeyboardButton(text="⚙️ Sozlamalar")],
    ]

    # Mini App tugmasi (WEBAPP_URL sozlangan bo'lsa)
    if WEBAPP_URL:
        keyboard.append([
            KeyboardButton(
                text="📱 Mini App",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Yozing yoki ovoz yuboring...",
    )
