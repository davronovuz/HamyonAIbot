"""Qarzlar API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import AsyncSessionFactory
from db.queries import (
    get_user_by_telegram_id, get_user_debts, get_debts_summary,
)
from web.auth import get_current_user

router = APIRouter(prefix="/debts", tags=["Debts"])


async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


@router.get("")
async def list_debts(
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Foydalanuvchining barcha qarzlari."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    debts = await get_user_debts(session, user.id)
    summary = await get_debts_summary(session, user.id)

    return {
        "debts": [
            {
                "id": d.id,
                "type": d.type,
                "person_name": d.person_name,
                "amount": float(d.amount),
                "paid_amount": float(d.paid_amount),
                "remaining": float(d.remaining_amount),
                "description": d.description,
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "is_paid": d.is_paid,
                "is_overdue": d.is_overdue,
                "created_at": d.created_at.isoformat(),
            }
            for d in debts
        ],
        "summary": {
            "total_lent": float(summary["total_lent"]),
            "total_borrowed": float(summary["total_borrowed"]),
            "lent_count": summary["lent_count"],
            "borrowed_count": summary["borrowed_count"],
        },
        "currency": user.currency,
    }
