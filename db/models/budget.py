from sqlalchemy import BigInteger, Numeric, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from db.base import Base


class Budget(Base):
    """
    Oylik byudjet — foydalanuvchi har bir kategoriya uchun
    oylik limit belgilashi mumkin. Limit oshsa ogohlantirish yuboriladi.
    """
    __tablename__ = "budgets"

    # Bir user, bir kategoriya, bir oy uchun faqat bitta budget bo'lishi kerak
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "year", "month", name="uq_budget_user_cat_period"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    # Oylik limit
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12

    # Limit oshganda ogohlantirish yuborilganmi
    alert_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="budgets", lazy="noload")  # noqa: F821
    category: Mapped["Category"] = relationship(back_populates="budgets", lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} user_id={self.user_id} "
            f"category_id={self.category_id} limit={self.monthly_limit} "
            f"{self.year}-{self.month:02d}>"
        )
