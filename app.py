import asyncio
import logging

from loader import dp, bot
from handlers import setup_handlers
from middlewares import ThrottlingMiddleware, DbSessionMiddleware
from services import create_scheduler


async def start_web_server():
    """FastAPI web serverni ishga tushirish (Mini App uchun)."""
    import uvicorn
    from web.server import app

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot():
    """Telegram botni ishga tushirish."""
    # Handlerlarni ulash
    main_router = setup_handlers()
    dp.include_router(main_router)

    # Middlewarelar
    dp.update.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottlingMiddleware(slow_mode_delay=1))

    # Scheduler ishga tushirish
    scheduler = create_scheduler(bot)
    scheduler.start()
    logging.info("Scheduler ishga tushdi.")

    logging.info("Bot ishga tushdi...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        logging.info("Scheduler to'xtatildi.")


async def main() -> None:
    """Bot va web server parallel ishlaydi."""
    await asyncio.gather(
        start_bot(),
        start_web_server(),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
