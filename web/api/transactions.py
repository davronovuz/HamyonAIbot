"""Tranzaksiyalar API."""
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import AsyncSessionFactory
from db.queries import (
    get_user_by_telegram_id,
    get_transactions_by_period,
    get_period_summary,
    get_category_breakdown,
    get_daily_stats_for_month,
    add_transaction,
    delete_transaction,
)
from db.models import TransactionType, InputSource
from web.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


@router.get("")
async def list_transactions(
    period: str = Query("month", pattern="^(today|week|month|all)$"),
    type: str | None = Query(None, pattern="^(income|expense)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Tranzaksiyalar ro'yxati — davr, tur bo'yicha filtrlash."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi", "transactions": []}

    today = date.today()
    if period == "today":
        date_from = today
    elif period == "week":
        date_from = today - timedelta(days=today.weekday())
    elif period == "month":
        date_from = today.replace(day=1)
    else:
        date_from = today - timedelta(days=365)

    type_filter = TransactionType(type) if type else None
    offset = (page - 1) * limit

    transactions = await get_transactions_by_period(
        session, user.id, date_from, today,
        type_filter=type_filter, limit=limit, offset=offset,
    )

    return {
        "transactions": [
            {
                "id": tx.id,
                "type": tx.type,
                "amount": float(tx.amount),
                "description": tx.description,
                "category": {
                    "id": tx.category.id,
                    "name": tx.category.name,
                    "icon": tx.category.icon,
                } if tx.category else None,
                "source": tx.source,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in transactions
        ],
        "page": page,
        "limit": limit,
        "currency": user.currency,
    }


@router.post("")
async def create_transaction(
    data: dict,
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Yangi tranzaksiya qo'shish."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    tx = await add_transaction(
        session=session,
        user_id=user.id,
        type=TransactionType(data["type"]),
        amount=Decimal(str(data["amount"])),
        category_id=data.get("category_id"),
        description=data.get("description"),
        source=InputSource.TEXT,
    )

    return {
        "id": tx.id,
        "type": tx.type,
        "amount": float(tx.amount),
        "description": tx.description,
        "created_at": tx.created_at.isoformat(),
    }


@router.delete("/{transaction_id}")
async def remove_transaction(
    transaction_id: int,
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Tranzaksiyani o'chirish."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    success = await delete_transaction(session, transaction_id, user.id)
    return {"success": success}


@router.get("/summary")
async def get_summary(
    period: str = Query("month", pattern="^(today|week|month)$"),
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Umumiy kirim/chiqim xulosa."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    today = date.today()
    if period == "today":
        date_from = today
    elif period == "week":
        date_from = today - timedelta(days=today.weekday())
    else:
        date_from = today.replace(day=1)

    summary = await get_period_summary(session, user.id, date_from, today)

    return {
        "total_income": float(summary["total_income"]),
        "total_expense": float(summary["total_expense"]),
        "balance": float(summary["balance"]),
        "transaction_count": summary["transaction_count"],
        "currency": user.currency,
        "date_from": date_from.isoformat(),
        "date_to": today.isoformat(),
    }


@router.get("/categories")
async def category_breakdown(
    period: str = Query("month", pattern="^(today|week|month)$"),
    type: str = Query("expense", pattern="^(income|expense)$"),
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Kategoriya bo'yicha taqsimot."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    today = date.today()
    if period == "today":
        date_from = today
    elif period == "week":
        date_from = today - timedelta(days=today.weekday())
    else:
        date_from = today.replace(day=1)

    rows = await get_category_breakdown(
        session, user.id, date_from, today, TransactionType(type)
    )

    return {
        "categories": [
            {
                "name": row["category_name"],
                "icon": row["icon"],
                "total": float(row["total"]),
                "percent": row["percent"],
            }
            for row in rows
        ],
        "currency": user.currency,
    }


@router.get("/daily-chart")
async def daily_chart_data(
    year: int = Query(None),
    month: int = Query(None),
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Kunlik grafik uchun data (oylik)."""
    user = await get_user_by_telegram_id(session, user_data["id"])
    if not user:
        return {"error": "Foydalanuvchi topilmadi"}

    today = date.today()
    y = year or today.year
    m = month or today.month

    stats = await get_daily_stats_for_month(session, user.id, y, m)

    return {
        "days": [
            {
                "day": s["day"],
                "income": float(s["income"]),
                "expense": float(s["expense"]),
            }
            for s in stats
        ],
        "year": y,
        "month": m,
        "currency": user.currency,
    }
