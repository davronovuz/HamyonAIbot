from sqlalchemy import BigInteger, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
import enum


class CategoryType(str, enum.Enum):
    INCOME = "income"    # Kirim
    EXPENSE = "expense"  # Chiqim
    BOTH = "both"        # Ikkalasi uchun ham (masalan "Boshqa")


# Default kategoriyalar - user ro'yxatdan o'tganda avtomatik yaratiladi
DEFAULT_CATEGORIES: list[dict] = [
    # Chiqim kategoriyalari
    {"name": "Oziq-ovqat", "type": CategoryType.EXPENSE, "icon": "🛒"},
    {"name": "Transport", "type": CategoryType.EXPENSE, "icon": "🚗"},
    {"name": "Kiyim-kechak", "type": CategoryType.EXPENSE, "icon": "👗"},
    {"name": "Uy-joy", "type": CategoryType.EXPENSE, "icon": "🏠"},
    {"name": "Kommunal", "type": CategoryType.EXPENSE, "icon": "💡"},
    {"name": "Sog'liq", "type": CategoryType.EXPENSE, "icon": "🏥"},
    {"name": "Ta'lim", "type": CategoryType.EXPENSE, "icon": "📚"},
    {"name": "Ko'ngilochar", "type": CategoryType.EXPENSE, "icon": "🎮"},
    {"name": "Sport", "type": CategoryType.EXPENSE, "icon": "⚽"},
    {"name": "Go'zallik", "type": CategoryType.EXPENSE, "icon": "💄"},
    {"name": "Sovg'a", "type": CategoryType.EXPENSE, "icon": "🎁"},
    {"name": "Sayohat", "type": CategoryType.EXPENSE, "icon": "✈️"},
    # Kirim kategoriyalari
    {"name": "Maosh", "type": CategoryType.INCOME, "icon": "💼"},
    {"name": "Freelance", "type": CategoryType.INCOME, "icon": "💻"},
    {"name": "Biznes", "type": CategoryType.INCOME, "icon": "🏪"},
    {"name": "Investitsiya", "type": CategoryType.INCOME, "icon": "📈"},
    {"name": "Sovrin", "type": CategoryType.INCOME, "icon": "🏆"},
    # Umumiy
    {"name": "Boshqa", "type": CategoryType.BOTH, "icon": "📦"},
]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="📦", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="categories", lazy="noload")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="category", lazy="noload"
    )
    budgets: Mapped[list["Budget"]] = relationship(  # noqa: F821
        back_populates="category", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name} type={self.type}>"
