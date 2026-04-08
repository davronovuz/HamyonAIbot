from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date, timedelta
from db.models.debt import Debt, DebtType


async def add_debt(
    session: AsyncSession,
    user_id: int,
    type: DebtType,
    person_name: str,
    amount: Decimal,
    description: str | None = None,
    due_date: date | None = None,
) -> Debt:
    """Yangi qarz qo'shish."""
    debt = Debt(
        user_id=user_id,
        type=type,
        person_name=person_name,
        amount=amount,
        description=description,
        due_date=due_date,
    )
    session.add(debt)
    await session.commit()
    await session.refresh(debt)
    return debt


async def get_user_debts(
    session: AsyncSession,
    user_id: int,
    type_filter: DebtType | None = None,
    active_only: bool = True,
) -> list[Debt]:
    """User qarzlarini olish."""
    query = select(Debt).where(Debt.user_id == user_id)

    if active_only:
        query = query.where(Debt.is_paid == False)  # noqa: E712

    if type_filter:
        query = query.where(Debt.type == type_filter)

    query = query.order_by(Debt.due_date.asc().nullslast(), Debt.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_debt_by_id(
    session: AsyncSession, debt_id: int, user_id: int
) -> Debt | None:
    """ID bo'yicha qarz topish."""
    result = await session.execute(
        select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def pay_debt_partial(
    session: AsyncSession,
    debt_id: int,
    user_id: int,
    pay_amount: Decimal,
) -> Debt | None:
    """Qarzni qisman yoki to'liq to'lash."""
    debt = await get_debt_by_id(session, debt_id, user_id)
    if not debt:
        return None

    new_paid = debt.paid_amount + pay_amount
    is_paid = new_paid >= debt.amount

    await session.execute(
        update(Debt)
        .where(Debt.id == debt_id, Debt.user_id == user_id)
        .values(
            paid_amount=min(new_paid, debt.amount),
            is_paid=is_paid,
        )
    )
    await session.commit()
    await session.refresh(debt)
    return debt


async def mark_debt_paid(
    session: AsyncSession, debt_id: int, user_id: int
) -> bool:
    """Qarzni to'liq to'langan deb belgilash."""
    result = await session.execute(
        update(Debt)
        .where(Debt.id == debt_id, Debt.user_id == user_id)
        .values(is_paid=True, paid_amount=Debt.amount)
    )
    await session.commit()
    return result.rowcount > 0


async def get_overdue_debts_for_reminder(session: AsyncSession) -> list[Debt]:
    """
    Eslatma yuborish kerak bo'lgan qarzlar.
    - Muddati 3 kun ichida yoki o'tib ketgan
    - Hali eslatma yuborilmagan
    - To'lanmagan
    """
    threshold = date.today() + timedelta(days=3)

    result = await session.execute(
        select(Debt).where(
            Debt.is_paid == False,          # noqa: E712
            Debt.reminder_sent == False,    # noqa: E712
            Debt.due_date <= threshold,
            Debt.due_date != None,          # noqa: E711
        )
    )
    return list(result.scalars().all())


async def mark_reminder_sent(session: AsyncSession, debt_id: int) -> None:
    """Eslatma yuborildi deb belgilash."""
    await session.execute(
        update(Debt).where(Debt.id == debt_id).values(reminder_sent=True)
    )
    await session.commit()


async def get_debts_summary(
    session: AsyncSession, user_id: int
) -> dict:
    """
    Qarzlar umumiy hisobi.
    Qaytaradi: {total_lent, total_borrowed, net_balance}
    """
    debts = await get_user_debts(session, user_id, active_only=True)

    total_lent = sum(d.remaining_amount for d in debts if d.type == DebtType.LENT)
    total_borrowed = sum(d.remaining_amount for d in debts if d.type == DebtType.BORROWED)

    return {
        "total_lent": total_lent,        # Men bergan (menga qaytarishadi)
        "total_borrowed": total_borrowed, # Men olgan (men qaytaraman)
        "net_balance": total_lent - total_borrowed,
        "lent_count": sum(1 for d in debts if d.type == DebtType.LENT),
        "borrowed_count": sum(1 for d in debts if d.type == DebtType.BORROWED),
    }
