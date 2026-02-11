"""Frontend routes for the dashboard page."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()
_STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@router.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")
