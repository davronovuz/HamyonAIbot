from decimal import Decimal
from datetime import date, datetime
from db.models.user import Currency


CURRENCY_SYMBOLS = {
    Currency.UZS: "so'm",
    Currency.USD: "$",
    Currency.RUB: "₽",
    Currency.EUR: "€",
}


def fmt_amount(amount: Decimal | float, currency: Currency = Currency.UZS) -> str:
    """Summani chiroyli formatda chiqarish. Masalan: 1 250 000 so'm"""
    amount = Decimal(str(amount))
    symbol = CURRENCY_SYMBOLS.get(currency, "so'm")

    if currency == Currency.UZS:
        # So'mda kasr ko'rsatilmaydi
        formatted = f"{int(amount):,}".replace(",", " ")
        return f"{formatted} {symbol}"
    else:
        formatted = f"{amount:,.2f}".replace(",", " ")
        return f"{formatted} {symbol}"


def fmt_date(d: date | datetime) -> str:
    """Sanani o'zbek formatida chiqarish. Masalan: 8-aprel, 2026"""
    months = [
        "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
        "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"
    ]
    if isinstance(d, datetime):
        d = d.date()
    return f"{d.day}-{months[d.month]}, {d.year}"


def fmt_period(date_from: date, date_to: date) -> str:
    """Davr nomini chiqarish."""
    if date_from == date_to:
        return fmt_date(date_from)
    return f"{fmt_date(date_from)} — {fmt_date(date_to)}"


def fmt_summary(summary: dict, currency: Currency = Currency.UZS) -> str:
    """Davr xulosasini chiroyli xabar sifatida formatlash."""
    income = fmt_amount(summary["total_income"], currency)
    expense = fmt_amount(summary["total_expense"], currency)
    balance = summary["balance"]
    balance_str = fmt_amount(abs(balance), currency)
    balance_sign = "+" if balance >= 0 else "-"
    balance_emoji = "📈" if balance >= 0 else "📉"

    period = fmt_period(summary["date_from"], summary["date_to"])

    return (
        f"<b>📊 {period}</b>\n\n"
        f"💚 Kirim: <b>{income}</b>\n"
        f"❤️ Chiqim: <b>{expense}</b>\n"
        f"{'─' * 20}\n"
        f"{balance_emoji} Balans: <b>{balance_sign}{balance_str}</b>\n\n"
        f"📝 Jami: {summary['transaction_count']} ta yozuv"
    )


def fmt_category_breakdown(rows: list[dict], currency: Currency = Currency.UZS) -> str:
    """Kategoriya bo'yicha xarajatlar ro'yxati."""
    if not rows:
        return "📭 Ma'lumot yo'q."

    lines = ["<b>📊 Kategoriya bo'yicha xarajatlar:</b>\n"]
    for row in rows:
        amount = fmt_amount(row["total"], currency)
        bar = "█" * int(row["percent"] / 10)
        lines.append(
            f"{row['icon']} <b>{row['category_name']}</b>\n"
            f"   {amount} ({row['percent']}%) {bar}"
        )
    return "\n".join(lines)


def fmt_debt(debt, currency: Currency = Currency.UZS) -> str:
    """Bitta qarz ma'lumotini formatlash."""
    from db.models.debt import DebtType

    type_emoji = "📤" if debt.type == DebtType.LENT else "📥"
    type_text = "Men berdim" if debt.type == DebtType.LENT else "Men oldim"

    remaining = fmt_amount(debt.remaining_amount, currency)
    total = fmt_amount(debt.amount, currency)

    text = (
        f"{type_emoji} <b>{debt.person_name}</b> — {type_text}\n"
        f"💰 Qolgan: <b>{remaining}</b> (jami: {total})\n"
    )

    if debt.due_date:
        due = fmt_date(debt.due_date)
        overdue = " ⚠️ <b>Muddati o'tdi!</b>" if debt.is_overdue else ""
        text += f"📅 Muddat: {due}{overdue}\n"

    if debt.description:
        text += f"📝 {debt.description}\n"

    return text.strip()
