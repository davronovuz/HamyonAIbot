from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.category import Category, CategoryType


async def get_user_categories(
    session: AsyncSession,
    user_id: int,
    type_filter: CategoryType | None = None,
    active_only: bool = True,
) -> list[Category]:
    """User kategoriyalarini olish, ixtiyoriy type filtr bilan."""
    query = select(Category).where(Category.user_id == user_id)

    if active_only:
        query = query.where(Category.is_active == True)  # noqa: E712

    if type_filter and type_filter != CategoryType.BOTH:
        # BOTH kategoriyalar har doim ko'rsatiladi
        query = query.where(
            (Category.type == type_filter) | (Category.type == CategoryType.BOTH)
        )

    query = query.order_by(Category.is_default.desc(), Category.name)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_category_by_id(
    session: AsyncSession, category_id: int, user_id: int
) -> Category | None:
    """ID bo'yicha kategoriya topish (user o'zining kategoriyasini topishi)."""
    result = await session.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_category_by_name(
    session: AsyncSession, user_id: int, name: str
) -> Category | None:
    """Nom bo'yicha kategoriya topish (AI parser uchun)."""
    result = await session.execute(
        select(Category).where(
            Category.user_id == user_id,
            Category.name.ilike(f"%{name}%"),
            Category.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create_category(
    session: AsyncSession,
    user_id: int,
    name: str,
    type: CategoryType,
    icon: str = "📦",
) -> Category:
    """Yangi kategoriya yaratish."""
    category = Category(
        user_id=user_id,
        name=name,
        type=type,
        icon=icon,
        is_default=False,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update_category(
    session: AsyncSession,
    category_id: int,
    user_id: int,
    name: str | None = None,
    icon: str | None = None,
) -> bool:
    """Kategoriya ma'lumotlarini yangilash. True qaytarsa muvaffaqiyatli."""
    values: dict = {}
    if name is not None:
        values["name"] = name
    if icon is not None:
        values["icon"] = icon

    if not values:
        return False

    result = await session.execute(
        update(Category)
        .where(Category.id == category_id, Category.user_id == user_id)
        .values(**values)
    )
    await session.commit()
    return result.rowcount > 0


async def deactivate_category(
    session: AsyncSession, category_id: int, user_id: int
) -> bool:
    """Kategoriyani o'chirish o'rniga deaktivlash (ma'lumotlar saqlanib qoladi)."""
    result = await session.execute(
        update(Category)
        .where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_default == False,  # noqa: E712
        )
        .values(is_active=False)
    )
    await session.commit()
    return result.rowcount > 0
