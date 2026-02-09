"""FOMC calendar source."""

from datetime import date


def fetch_fomc_schedule() -> dict:
    return {
        "next_meeting": date(2026, 3, 18).isoformat(),
        "next_meeting_type": "Rate decision",
        "source": "Federal Reserve (placeholder)",
    }
