"""Kategoriyalar API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import AsyncSessionFactory
from db.queries import get_user_by_telegram_id, get_user_categories
from db.models import TransactionType
from web.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


@router.get("")
async def list_categories(
    type: str | None = Query(None, pattern="^(income|expense)$"),
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Foydalanuvchining kategoriyalari."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    type_filter = TransactionType(type) if type else None
    categories = await get_user_categories(session, user.id, type_filter=type_filter)

    return {
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "icon": c.icon,
                "is_default": c.is_default,
            }
            for c in categories
        ],
    }
