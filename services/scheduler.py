"""
Scheduler — avtomatik eslatmalar va hisobotlar.
APScheduler async mode da ishlaydi.

Joblar:
  - 09:00 — qarz eslatmalari (muddati 3 kun ichida yoki o'tgan)
  - 21:00 — kunlik hisobot (bugungi kirim/chiqim xulosa)
  - Dushanba 10:00 — haftalik hisobot
  - Har oyning 1-kuni 10:00 — oylik hisobot
"""
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from db.base import AsyncSessionFactory
from db.queries import (
    get_all_active_users,
    get_period_summary,
    get_category_breakdown,
    get_overdue_debts_for_reminder,
    mark_reminder_sent,
)
from db.models import TransactionType
from utils import fmt_summary, fmt_amount, fmt_date

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# KUNLIK HISOBOT — har kuni 21:00
# ──────────────────────────────────────────────

async def send_daily_reports(bot: Bot) -> None:
    logger.info("Kunlik hisobotlar yuborilmoqda...")
    today = date.today()

    async with AsyncSessionFactory() as session:
        users = await get_all_active_users(session)

        for user in users:
            if not user.daily_report:
                continue
            try:
                summary = await get_period_summary(session, user.id, today, today)

                if summary["transaction_count"] == 0:
                    continue  # Bugun hech narsa kiritmagan — xabar yubormaymiz

                text = (
                    f"🌙 <b>Kunlik hisobot</b>\n\n"
                    + fmt_summary(summary, user.currency)
                )

                # Top-3 xarajat kategoriyasi
                breakdown = await get_category_breakdown(
                    session, user.id, today, today, TransactionType.EXPENSE
                )
                if breakdown:
                    text += "\n\n<b>Top xarajatlar:</b>\n"
                    for row in breakdown[:3]:
                        amount = fmt_amount(row["total"], user.currency)
                        text += f"{row['icon']} {row['category_name']}: {amount}\n"

                await bot.send_message(user.telegram_id, text)

            except Exception as e:
                logger.error(f"Kunlik hisobot xatoligi (user {user.telegram_id}): {e}")


# ──────────────────────────────────────────────
# HAFTALIK HISOBOT — Dushanba 10:00
# ──────────────────────────────────────────────

async def send_weekly_reports(bot: Bot) -> None:
    logger.info("Haftalik hisobotlar yuborilmoqda...")
    today = date.today()
    week_start = today - timedelta(days=7)

    async with AsyncSessionFactory() as session:
        users = await get_all_active_users(session)

        for user in users:
            if not user.weekly_report:
                continue
            try:
                summary = await get_period_summary(session, user.id, week_start, today)

                if summary["transaction_count"] == 0:
                    continue

                breakdown = await get_category_breakdown(
                    session, user.id, week_start, today, TransactionType.EXPENSE
                )

                text = (
                    f"📆 <b>Haftalik hisobot</b>\n\n"
                    + fmt_summary(summary, user.currency)
                )

                if breakdown:
                    text += "\n\n<b>Xarajatlar taqsimoti:</b>\n"
                    for row in breakdown[:5]:
                        amount = fmt_amount(row["total"], user.currency)
                        text += f"{row['icon']} {row['category_name']}: {amount} ({row['percent']}%)\n"

                await bot.send_message(user.telegram_id, text)

            except Exception as e:
                logger.error(f"Haftalik hisobot xatoligi (user {user.telegram_id}): {e}")


# ──────────────────────────────────────────────
# OYLIK HISOBOT — har oyning 1-kuni 10:00
# ──────────────────────────────────────────────

async def send_monthly_reports(bot: Bot) -> None:
    logger.info("Oylik hisobotlar yuborilmoqda...")
    today = date.today()
    # O'tgan oyning 1-kuni va oxirgi kuni
    first_day_this_month = today.replace(day=1)
    last_month_end = first_day_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    months_uz = [
        "", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
    ]
    month_name = months_uz[last_month_end.month]

    async with AsyncSessionFactory() as session:
        users = await get_all_active_users(session)

        for user in users:
            if not user.monthly_report:
                continue
            try:
                summary = await get_period_summary(session, user.id, last_month_start, last_month_end)

                if summary["transaction_count"] == 0:
                    continue

                breakdown = await get_category_breakdown(
                    session, user.id, last_month_start, last_month_end, TransactionType.EXPENSE
                )

                income = fmt_amount(summary["total_income"], user.currency)
                expense = fmt_amount(summary["total_expense"], user.currency)
                balance = summary["balance"]
                balance_str = fmt_amount(abs(balance), user.currency)
                balance_sign = "+" if balance >= 0 else "-"
                balance_emoji = "📈" if balance >= 0 else "📉"

                text = (
                    f"🗓 <b>{month_name} {last_month_end.year} — Oylik hisobot</b>\n\n"
                    f"💚 Kirim: <b>{income}</b>\n"
                    f"❤️ Chiqim: <b>{expense}</b>\n"
                    f"{'─' * 20}\n"
                    f"{balance_emoji} Balans: <b>{balance_sign}{balance_str}</b>\n\n"
                    f"📝 Jami: {summary['transaction_count']} ta yozuv\n"
                )

                if breakdown:
                    text += "\n<b>Top-5 xarajat kategoriyasi:</b>\n"
                    for row in breakdown[:5]:
                        amount = fmt_amount(row["total"], user.currency)
                        bar_count = max(1, int(row["percent"] / 10))
                        bar = "█" * bar_count
                        text += f"{row['icon']} {row['category_name']}: {amount} {bar}\n"

                await bot.send_message(user.telegram_id, text)

            except Exception as e:
                logger.error(f"Oylik hisobot xatoligi (user {user.telegram_id}): {e}")


# ──────────────────────────────────────────────
# QARZ ESLATMALARI — har kuni 09:00
# ──────────────────────────────────────────────

async def send_debt_reminders(bot: Bot) -> None:
    logger.info("Qarz eslatmalari yuborilmoqda...")

    async with AsyncSessionFactory() as session:
        debts = await get_overdue_debts_for_reminder(session)

        for debt in debts:
            try:
                # User ni topish
                from db.queries import get_user_by_telegram_id
                from sqlalchemy import select
                from db.models import User
                result = await session.execute(
                    select(User).where(User.id == debt.user_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    continue

                from db.models.debt import DebtType
                from utils import fmt_amount

                amount = fmt_amount(debt.remaining_amount, user.currency)
                type_emoji = "📤" if debt.type == DebtType.LENT else "📥"
                type_text = (
                    f"<b>{debt.person_name}</b> sizga qaytarishi kerak"
                    if debt.type == DebtType.LENT
                    else f"Siz <b>{debt.person_name}</b> ga qaytarishingiz kerak"
                )

                if debt.is_overdue:
                    due_text = f"⚠️ Muddati o'tdi: {fmt_date(debt.due_date)}"
                else:
                    days_left = (debt.due_date - date.today()).days
                    due_text = f"📅 {days_left} kun qoldi ({fmt_date(debt.due_date)})"

                text = (
                    f"{type_emoji} <b>Qarz eslatmasi</b>\n\n"
                    f"{type_text}\n"
                    f"💰 Miqdor: <b>{amount}</b>\n"
                    f"{due_text}"
                )

                await bot.send_message(user.telegram_id, text)
                await mark_reminder_sent(session, debt.id)

            except Exception as e:
                logger.error(f"Qarz eslatma xatoligi (debt {debt.id}): {e}")


# ──────────────────────────────────────────────
# SCHEDULER SETUP
# ──────────────────────────────────────────────

def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Qarz eslatmalari — har kuni 09:00
    scheduler.add_job(
        send_debt_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        kwargs={"bot": bot},
        id="debt_reminders",
        replace_existing=True,
    )

    # Kunlik hisobot — har kuni 21:00
    scheduler.add_job(
        send_daily_reports,
        trigger=CronTrigger(hour=21, minute=0),
        kwargs={"bot": bot},
        id="daily_reports",
        replace_existing=True,
    )

    # Haftalik hisobot — Dushanba 10:00
    scheduler.add_job(
        send_weekly_reports,
        trigger=CronTrigger(day_of_week="mon", hour=10, minute=0),
        kwargs={"bot": bot},
        id="weekly_reports",
        replace_existing=True,
    )

    # Oylik hisobot — har oyning 1-kuni 10:00
    scheduler.add_job(
        send_monthly_reports,
        trigger=CronTrigger(day=1, hour=10, minute=0),
        kwargs={"bot": bot},
        id="monthly_reports",
        replace_existing=True,
    )

    return scheduler
