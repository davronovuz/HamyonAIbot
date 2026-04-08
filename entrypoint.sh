#!/bin/sh
set -e

echo "⏳ PostgreSQL tayyor bo'lishini kutmoqda..."

until python3 -c "
import asyncio, asyncpg, os, sys
async def check():
    try:
        url = os.environ['DB_URL'].replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(url)
        await conn.close()
    except Exception:
        sys.exit(1)
asyncio.run(check())
" 2>/dev/null; do
    echo "   DB hali tayyor emas, 2 sekunddan keyin qayta..."
    sleep 2
done

echo "✅ PostgreSQL tayyor."
echo "🔄 Migratsiyalar ishga tushirilmoqda..."

alembic upgrade head

echo "✅ Migratsiyalar tugadi."
echo "🚀 Bot ishga tushmoqda..."
exec python3 app.py
