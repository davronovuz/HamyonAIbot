from dotenv import load_dotenv
import os

load_dotenv()

# Telegram
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMINS: list[int] = [int(i) for i in os.getenv("ADMINS", "").split(",") if i.strip()]

# PostgreSQL — asyncpg uchun postgresql+asyncpg:// prefix
DB_URL: str = os.getenv("DB_URL", "postgresql+asyncpg://user:password@localhost:5432/hamyonai")

# OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Ixtiyoriy: webhook (polling o'rniga)
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL: str = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Xarajat limiti ogohlantirish foizi
BUDGET_WARNING_THRESHOLD: int = 80   # 80% da ogohlantirish
BUDGET_EXCEEDED_THRESHOLD: int = 100 # 100% da xabar

# Qarz eslatma (necha kun oldin)
DEBT_REMINDER_DAYS: int = int(os.getenv("DEBT_REMINDER_DAYS", "3"))
