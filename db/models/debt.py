from sqlalchemy import BigInteger, Numeric, String, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from datetime import date
from db.base import Base
import enum


class DebtType(str, enum.Enum):
    LENT = "lent"       # Men boshqaga berdim (menga qaytarishi kerak)
    BORROWED = "borrowed"  # Men boshqadan oldim (men qaytarishim kerak)


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Qarz bergan/olgan odam ismi
    person_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Qarz miqdori
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # To'langan summa (qisman to'lashga imkon)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Qaytarish muddati
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # To'liq yopilib, tugaganmi
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Eslatma yuborilganmi (scheduler uchun)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="debts", lazy="noload")  # noqa: F821

    @property
    def remaining_amount(self) -> Decimal:
        """Qolgan qarz miqdori."""
        return self.amount - self.paid_amount

    @property
    def is_overdue(self) -> bool:
        """Muddati o'tganmi."""
        if self.due_date is None or self.is_paid:
            return False
        return date.today() > self.due_date

    def __repr__(self) -> str:
        return (
            f"<Debt id={self.id} type={self.type} "
            f"person={self.person_name} amount={self.amount}>"
        )
