"""API routes for actionable trading signals."""

from fastapi import APIRouter, Query

from services.signal_service import get_signal_service

router = APIRouter()


@router.get("/latest")
def latest_signals() -> dict:
    service = get_signal_service()
    return {
        "signals": service.latest_signals(),
        "data_health": service.data_health(),
    }


@router.get("/{symbol}")
def symbol_signals(symbol: str, limit: int = Query(default=40, ge=1, le=500)) -> dict:
    service = get_signal_service()
    return {
        "symbol": symbol.upper(),
        "signals": service.signals_for_symbol(symbol=symbol, limit=limit),
    }
