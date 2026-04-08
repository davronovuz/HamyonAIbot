from aiogram import Router
from .start import router as start_router
from .transaction import router as transaction_router
from .history import router as history_router
from .reports import router as reports_router
from .debts import router as debts_router
from .settings import router as settings_router
from .admins import router as admins_router
from .echo import router as echo_router  # eng oxirida — barcha noma'lum xabarlar


def setup_handlers() -> Router:
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(admins_router)
    main_router.include_router(transaction_router)
    main_router.include_router(history_router)
    main_router.include_router(reports_router)
    main_router.include_router(debts_router)
    main_router.include_router(settings_router)
    main_router.include_router(echo_router)  # DOIM eng oxirida bo'lishi shart

    return main_router
