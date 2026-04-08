from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
import enum


class Language(str, enum.Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class Currency(str, enum.Enum):
    UZS = "UZS"
    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="uz", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Daily/weekly/monthly hisobot yuborish sozlamasi
    daily_report: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_report: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monthly_report: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )
    categories: Mapped[list["Category"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )
    debts: Mapped[list["Debt"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )
    budgets: Mapped[list["Budget"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} name={self.full_name}>"
