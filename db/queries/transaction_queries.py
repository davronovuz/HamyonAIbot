from sqlalchemy import select, func, and_, extract, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import date, datetime, timedelta
from db.models.transaction import Transaction, TransactionType, InputSource
from db.models.category import Category


async def add_transaction(
    session: AsyncSession,
    user_id: int,
    type: TransactionType,
    amount: Decimal,
    category_id: int | None = None,
    description: str | None = None,
    voice_text: str | None = None,
    source: InputSource = InputSource.TEXT,
) -> Transaction:
    """Yangi tranzaksiya qo'shish."""
    tx = Transaction(
        user_id=user_id,
        type=type,
        amount=amount,
        category_id=category_id,
        description=description,
        voice_text=voice_text,
        source=source,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def get_transactions_by_period(
    session: AsyncSession,
    user_id: int,
    date_from: date,
    date_to: date,
    type_filter: TransactionType | None = None,
    category_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Transaction]:
    """Davr bo'yicha tranzaksiyalarni olish."""
    query = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.user_id == user_id,
            func.date(Transaction.created_at) >= date_from,
            func.date(Transaction.created_at) <= date_to,
        )
    )

    if type_filter:
        query = query.where(Transaction.type == type_filter)

    if category_id:
        query = query.where(Transaction.category_id == category_id)

    query = query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_today_transactions(
    session: AsyncSession, user_id: int
) -> list[Transaction]:
    """Bugungi tranzaksiyalar."""
    today = date.today()
    return await get_transactions_by_period(session, user_id, today, today)


async def get_period_summary(
    session: AsyncSession,
    user_id: int,
    date_from: date,
    date_to: date,
) -> dict:
    """
    Davr uchun umumiy statistika.
    Qaytaradi: {total_income, total_expense, balance, transaction_count}
    """
    result = await session.execute(
        select(
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.user_id == user_id,
            func.date(Transaction.created_at) >= date_from,
            func.date(Transaction.created_at) <= date_to,
        )
        .group_by(Transaction.type)
    )

    rows = result.all()
    income = Decimal("0")
    expense = Decimal("0")
    count = 0

    for row in rows:
        if row.type == TransactionType.INCOME:
            income = row.total or Decimal("0")
        else:
            expense = row.total or Decimal("0")
        count += row.count

    return {
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
        "transaction_count": count,
        "date_from": date_from,
        "date_to": date_to,
    }


async def get_category_breakdown(
    session: AsyncSession,
    user_id: int,
    date_from: date,
    date_to: date,
    type_filter: TransactionType = TransactionType.EXPENSE,
) -> list[dict]:
    """
    Kategoriya bo'yicha xarajatlar tahlili.
    Qaytaradi: [{category_name, icon, total, percent}, ...]
    """
    result = await session.execute(
        select(
            Category.name,
            Category.icon,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == type_filter,
            func.date(Transaction.created_at) >= date_from,
            func.date(Transaction.created_at) <= date_to,
        )
        .group_by(Category.name, Category.icon)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = result.all()
    grand_total = sum(row.total for row in rows if row.total) or Decimal("1")

    return [
        {
            "category_name": row.name or "Boshqa",
            "icon": row.icon or "📦",
            "total": row.total or Decimal("0"),
            "percent": round((row.total or Decimal("0")) / grand_total * 100, 1),
        }
        for row in rows
    ]


async def get_daily_stats_for_month(
    session: AsyncSession,
    user_id: int,
    year: int,
    month: int,
) -> list[dict]:
    """
    Oylik kunlik statistika (grafik uchun).
    Qaytaradi: [{day, income, expense}, ...]
    """
    result = await session.execute(
        select(
            extract("day", Transaction.created_at).label("day"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            extract("year", Transaction.created_at) == year,
            extract("month", Transaction.created_at) == month,
        )
        .group_by(
            extract("day", Transaction.created_at),
            Transaction.type,
        )
        .order_by(extract("day", Transaction.created_at))
    )

    rows = result.all()

    # Kunlar bo'yicha birlashtirish
    daily: dict[int, dict] = {}
    for row in rows:
        day = int(row.day)
        if day not in daily:
            daily[day] = {"day": day, "income": Decimal("0"), "expense": Decimal("0")}
        if row.type == TransactionType.INCOME:
            daily[day]["income"] = row.total or Decimal("0")
        else:
            daily[day]["expense"] = row.total or Decimal("0")

    return sorted(daily.values(), key=lambda x: x["day"])


async def delete_transaction(
    session: AsyncSession, transaction_id: int, user_id: int
) -> bool:
    """Tranzaksiyani o'chirish. True qaytarsa muvaffaqiyatli."""
    result = await session.execute(
        delete(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    await session.commit()
    return result.rowcount > 0


async def get_transaction_by_id(
    session: AsyncSession, transaction_id: int, user_id: int
) -> Transaction | None:
    """ID bo'yicha tranzaksiya topish."""
    result = await session.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
