"""initial_tables

Revision ID: 0001
Revises:
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUM types
    op.execute("CREATE TYPE language_enum AS ENUM ('uz', 'ru', 'en')")
    op.execute("CREATE TYPE currency_enum AS ENUM ('UZS', 'USD', 'RUB', 'EUR')")
    op.execute("CREATE TYPE category_type_enum AS ENUM ('income', 'expense', 'both')")
    op.execute("CREATE TYPE transaction_type_enum AS ENUM ('income', 'expense')")
    op.execute("CREATE TYPE input_source_enum AS ENUM ('text', 'voice', 'quick')")
    op.execute("CREATE TYPE debt_type_enum AS ENUM ('lent', 'borrowed')")

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("language", sa.Enum("uz", "ru", "en", name="language_enum"), nullable=False, server_default="uz"),
        sa.Column("currency", sa.Enum("UZS", "USD", "RUB", "EUR", name="currency_enum"), nullable=False, server_default="UZS"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("daily_report", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("weekly_report", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("monthly_report", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # categories
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.Enum("income", "expense", "both", name="category_type_enum"), nullable=False),
        sa.Column("icon", sa.String(10), nullable=False, server_default="📦"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("category_id", sa.BigInteger, sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.Enum("income", "expense", name="transaction_type_enum"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("voice_text", sa.Text, nullable=True),
        sa.Column("source", sa.Enum("text", "voice", "quick", name="input_source_enum"), nullable=False, server_default="text"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # debts
    op.create_table(
        "debts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.Enum("lent", "borrowed", name="debt_type_enum"), nullable=False),
        sa.Column("person_name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("is_paid", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("reminder_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # budgets
    op.create_table(
        "budgets",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("category_id", sa.BigInteger, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(15, 2), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("alert_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "category_id", "year", "month", name="uq_budget_user_cat_period"),
    )


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("debts")
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS debt_type_enum")
    op.execute("DROP TYPE IF EXISTS input_source_enum")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum")
    op.execute("DROP TYPE IF EXISTS category_type_enum")
    op.execute("DROP TYPE IF EXISTS currency_enum")
    op.execute("DROP TYPE IF EXISTS language_enum")
