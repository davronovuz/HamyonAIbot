from sqlalchemy import BigInteger, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from db.base import Base
import enum


class TransactionType(str, enum.Enum):
    INCOME = "income"    # Kirim
    EXPENSE = "expense"  # Chiqim


class InputSource(str, enum.Enum):
    TEXT = "text"    # Qo'lda kiritilgan
    VOICE = "voice"  # Ovozli xabar orqali
    QUICK = "quick"  # Tezkor tugmalar orqali


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Numeric(15, 2) — 15 ta raqam, 2 ta kasr
    # Masalan: 999_999_999_999_999.99 (yetarli darajada katta)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Ovoz matni (agar voice orqali kiritilgan bo'lsa)
    voice_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Qaysi usulda kiritilgan
    source: Mapped[str] = mapped_column(String(20), default="text", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="transactions", lazy="noload")  # noqa: F821
    category: Mapped["Category | None"] = relationship(  # noqa: F821
        back_populates="transactions", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.type} "
            f"amount={self.amount} user_id={self.user_id}>"
        )
