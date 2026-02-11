"""ISM PMI data source (placeholder — ISM PMI is proprietary, not available on FRED)."""

from datetime import date


def fetch_ism_services_pmi() -> dict:
    """Return placeholder ISM PMI data.

    ISM Manufacturing PMI is proprietary data not freely available via API.
    The FRED series NAPM has been discontinued.
    """
    return {
        "period": "2026-01",
        "headline": 52.4,
        "headline_prev": 54.1,
        "headline_expected": None,
        "release_date": date(2026, 2, 3).isoformat(),
        "source": "ISM (placeholder)",
        "is_placeholder": True,
    }
