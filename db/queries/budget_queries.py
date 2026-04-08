from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import date
from db.models.budget import Budget
from db.models.transaction import Transaction, TransactionType


async def set_budget(
    session: AsyncSession,
    user_id: int,
    category_id: int,
    monthly_limit: Decimal,
    year: int | None = None,
    month: int | None = None,
) -> Budget:
    """Kategoriya uchun byudjet o'rnatish (mavjud bo'lsa yangilash)."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    # Mavjud byudjetni tekshirish
    result = await session.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.year == year,
            Budget.month == month,
        )
    )
    budget = result.scalar_one_or_none()

    if budget:
        await session.execute(
            update(Budget)
            .where(Budget.id == budget.id)
            .values(monthly_limit=monthly_limit, alert_sent=False)
        )
        await session.commit()
        await session.refresh(budget)
        return budget

    budget = Budget(
        user_id=user_id,
        category_id=category_id,
        monthly_limit=monthly_limit,
        year=year,
        month=month,
    )
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    return budget


async def get_user_budgets(
    session: AsyncSession,
    user_id: int,
    year: int | None = None,
    month: int | None = None,
) -> list[Budget]:
    """Usening joriy oy byudjetlarini olish."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    result = await session.execute(
        select(Budget)
        .options(joinedload(Budget.category))
        .where(
            Budget.user_id == user_id,
            Budget.year == year,
            Budget.month == month,
        )
    )
    return list(result.scalars().all())


async def check_budget_alerts(
    session: AsyncSession,
    user_id: int,
    category_id: int,
    year: int | None = None,
    month: int | None = None,
) -> dict | None:
    """
    Kategoriya byudjeti limitga yaqinlashganini tekshirish.
    80% dan oshsa ogohlantirish, 100% oshsa xabar.
    Qaytaradi: {budget, spent, percent, alert_type} yoki None
    """
    today = date.today()
    year = year or today.year
    month = month or today.month

    # Byudjetni topish
    result = await session.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.year == year,
            Budget.month == month,
            Budget.alert_sent == False,  # noqa: E712
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        return None

    # Joriy oy sarfini hisoblash
    from sqlalchemy import extract, func
    spent_result = await session.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == TransactionType.EXPENSE,
            extract("year", Transaction.created_at) == year,
            extract("month", Transaction.created_at) == month,
        )
    )
    spent = spent_result.scalar() or Decimal("0")
    percent = (spent / budget.monthly_limit * 100) if budget.monthly_limit else 0

    if percent >= 100:
        return {"budget": budget, "spent": spent, "percent": percent, "alert_type": "exceeded"}
    elif percent >= 80:
        return {"budget": budget, "spent": spent, "percent": percent, "alert_type": "warning"}

    return None


async def mark_budget_alert_sent(session: AsyncSession, budget_id: int) -> None:
    """Byudjet ogohlantirmasi yuborildi deb belgilash."""
    await session.execute(
        update(Budget).where(Budget.id == budget_id).values(alert_sent=True)
    )
    await session.commit()
