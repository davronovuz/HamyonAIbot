"""
Telegram Mini App autentifikatsiyasi.
initData ni tekshirish va foydalanuvchini aniqlash.
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
from urllib.parse import unquote, parse_qsl

from fastapi import Request, HTTPException

from data.config import BOT_TOKEN


def validate_init_data(init_data: str) -> dict:
    """
    Telegram initData ni tekshirish.
    Muvaffaqiyatli bo'lsa user ma'lumotlarini qaytaradi.
    """
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in parsed:
        raise ValueError("hash topilmadi")

    received_hash = parsed.pop("hash")

    # data-check-string yaratish (alifbo tartibida)
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    # calculated_hash = HMAC-SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("initData imzosi noto'g'ri")

    # User ma'lumotlarini ajratish
    user_data = json.loads(unquote(parsed.get("user", "{}")))
    return user_data


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency — Telegram foydalanuvchisini aniqlash.
    Authorization header dan initData olinadi.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("tma "):
        raise HTTPException(status_code=401, detail="Authorization header kerak (tma <initData>)")

    init_data = auth_header[4:]  # "tma " ni olib tashlash

    try:
        user_data = validate_init_data(init_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if "id" not in user_data:
        raise HTTPException(status_code=401, detail="User ID topilmadi")

    return user_data
