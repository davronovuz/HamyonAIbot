"""
FastAPI web server — Telegram Mini App uchun backend.
Bot bilan birgalikda asyncio da ishlaydi.
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from web.api.transactions import router as transactions_router
from web.api.debts import router as debts_router
from web.api.categories import router as categories_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HamyonAI Mini App",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS — Telegram Mini App ichidan so'rov yuborishga ruxsat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routerlar
app.include_router(transactions_router, prefix="/api")
app.include_router(debts_router, prefix="/api")
app.include_router(categories_router, prefix="/api")

# Static files — React build
STATIC_DIR = Path(__file__).parent.parent / "webapp" / "dist"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
