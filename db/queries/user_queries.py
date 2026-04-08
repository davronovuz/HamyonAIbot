from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User, Language, Currency
from db.models.category import Category, DEFAULT_CATEGORIES


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Telegram ID bo'yicha userni topish."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
    language: Language = Language.UZ,
    currency: Currency = Currency.UZS,
) -> User:
    """Yangi user yaratish va default kategoriyalarni qo'shish."""
    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
        language=language,
        currency=currency,
    )
    session.add(user)
    await session.flush()  # user.id ni olish uchun

    # Default kategoriyalarni qo'shish
    categories = [
        Category(
            user_id=user.id,
            name=cat["name"],
            type=cat["type"],
            icon=cat["icon"],
            is_default=True,
        )
        for cat in DEFAULT_CATEGORIES
    ]
    session.add_all(categories)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
) -> tuple[User, bool]:
    """User topish yoki yangi yaratish. (user, is_new) qaytaradi."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        # Ismini yangilab qo'yamiz (o'zgargan bo'lishi mumkin)
        if user.full_name != full_name or user.username != username:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(full_name=full_name, username=username)
            )
            await session.commit()
            await session.refresh(user)
        return user, False

    user = await create_user(session, telegram_id, full_name, username)
    return user, True


async def update_user_language(
    session: AsyncSession, telegram_id: int, language: Language
) -> None:
    """User tilini o'zgartirish."""
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(language=language)
    )
    await session.commit()


async def update_user_currency(
    session: AsyncSession, telegram_id: int, currency: Currency
) -> None:
    """User valyutasini o'zgartirish."""
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(currency=currency)
    )
    await session.commit()


async def update_user_report_settings(
    session: AsyncSession,
    telegram_id: int,
    daily_report: bool | None = None,
    weekly_report: bool | None = None,
    monthly_report: bool | None = None,
) -> None:
    """Hisobot sozlamalarini yangilash."""
    values: dict = {}
    if daily_report is not None:
        values["daily_report"] = daily_report
    if weekly_report is not None:
        values["weekly_report"] = weekly_report
    if monthly_report is not None:
        values["monthly_report"] = monthly_report

    if values:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(**values)
        )
        await session.commit()


async def get_all_active_users(session: AsyncSession) -> list[User]:
    """Barcha aktiv userlarni olish (scheduler uchun)."""
    result = await session.execute(
        select(User).where(User.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())
