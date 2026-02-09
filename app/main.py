"""FastAPI entrypoint for macro crypto report service."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes.frontend import router as frontend_router
from app.routes.regime import router as regime_router
from app.routes.report import router as report_router
from app.routes.signals import router as signals_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(frontend_router, tags=["frontend"])
    app.include_router(report_router, prefix="/report", tags=["report"])
    app.include_router(signals_router, prefix="/signals", tags=["signals"])
    app.include_router(regime_router, prefix="/regime", tags=["regime"])
    return app


app = create_app()
