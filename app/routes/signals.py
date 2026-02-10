"""API routes for actionable trading signals."""

import re

from fastapi import APIRouter, HTTPException, Query

from services.signal_service import get_signal_service

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,20}$")

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
    symbol = symbol.upper()
    if not _SYMBOL_PATTERN.match(symbol):
        raise HTTPException(status_code=422, detail="Invalid symbol format")
    service = get_signal_service()
    return {
        "symbol": symbol,
        "signals": service.signals_for_symbol(symbol=symbol, limit=limit),
    }
