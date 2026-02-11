"""FastAPI entrypoint for macro crypto report service."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)
from app.routes.frontend import router as frontend_router
from app.routes.regime import router as regime_router
from app.routes.report import router as report_router
from app.routes.signals import router as signals_router


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(frontend_router, tags=["frontend"])
    app.include_router(report_router, prefix="/report", tags=["report"])
    app.include_router(signals_router, prefix="/signals", tags=["signals"])
    app.include_router(regime_router, prefix="/regime", tags=["regime"])

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": str(exc)},
        )

    return app


app = create_app()
