from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
from data.config import DB_URL


engine = create_async_engine(
    DB_URL,
    echo=False,          # True qilsangiz SQL loglar chiqadi (debug uchun)
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Ulanish siniq bo'lsa avtomatik qayta ulash
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit dan keyin objectlar yuklanmay qolmasin
    autoflush=False,
)


class Base(DeclarativeBase):
    """Barcha modellar uchun asosiy Base class."""

    # Har bir modelda avtomatik created_at va updated_at bo'lsin
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def create_tables() -> None:
    """Barcha jadvallarni yaratish (development uchun).
    Production da Alembic migration ishlatilsin."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Barcha jadvallarni o'chirish (faqat test uchun!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
