"""FOMC calendar source (static 2025-2026 schedule)."""

from datetime import date

# Official FOMC meeting dates (announcement day)
# Source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
FOMC_DATES = [
    # 2025
    date(2025, 1, 29),
    date(2025, 3, 19),
    date(2025, 5, 7),
    date(2025, 6, 18),
    date(2025, 7, 30),
    date(2025, 9, 17),
    date(2025, 10, 29),
    date(2025, 12, 17),
    # 2026
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 10, 28),
    date(2026, 12, 16),
]


def fetch_fomc_schedule() -> dict:
    """Find the next upcoming FOMC meeting from the static calendar."""
    today = date.today()
    next_meeting = None
    for d in FOMC_DATES:
        if d >= today:
            next_meeting = d
            break

    if next_meeting is None:
        # All dates passed; return last known + note
        next_meeting = FOMC_DATES[-1]

    return {
        "next_meeting": next_meeting.isoformat(),
        "next_meeting_type": "Rate decision",
        "source": "Federal Reserve (static calendar)",
        "is_placeholder": False,
    }
