"""ISM PMI data source."""

from datetime import date


def fetch_ism_services_pmi() -> dict:
    return {
        "period": "2026-01",
        "headline": 52.4,
        "release_date": date(2026, 2, 3).isoformat(),
        "source": "ISM (placeholder)",
    }
