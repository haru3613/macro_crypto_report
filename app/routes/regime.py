"""API route for current regime state."""

from fastapi import APIRouter

from services.signal_service import get_signal_service

router = APIRouter()


@router.get("/current")
def current_regime() -> dict:
    service = get_signal_service()
    return {
        "regime": service.current_regime(),
        "data_health": service.data_health(),
    }
