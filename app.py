import asyncio
import logging

from loader import dp, bot
from handlers import setup_handlers
from middlewares import ThrottlingMiddleware, DbSessionMiddleware
from services import create_scheduler


async def main() -> None:
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
