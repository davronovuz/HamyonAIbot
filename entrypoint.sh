#!/bin/sh
set -e

echo "⏳ PostgreSQL tayyor bo'lishini kutmoqda..."

# DB ulanguncha kutamiz (max 30 sekund)
until python3 -c "
import asyncio, asyncpg, os, sys
async def check():
    try:
        conn = await asyncpg.connect(os.environ['DB_URL'].replace('postgresql+asyncpg://', 'postgresql://'))
        await conn.close()
    except Exception as e:
        sys.exit(1)
asyncio.run(check())
" 2>/dev/null; do
    echo "   DB hali tayyor emas, 2 sekunddan keyin qayta..."
    sleep 2
done

echo "✅ PostgreSQL tayyor."

echo "🔄 Migratsiyalar ishga tushirilmoqda..."
alembic upgrade head

echo "🚀 Bot ishga tushmoqda..."
exec python3 app.py
