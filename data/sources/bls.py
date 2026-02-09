"""BLS macro data sources (CPI, NFP)."""

from datetime import date


def fetch_cpi() -> dict:
    """Fetch latest CPI values (placeholder)."""
    return {
        "period": "2026-01",
        "headline_yoy": 3.1,
        "core_yoy": 3.3,
        "release_date": date(2026, 2, 13).isoformat(),
        "source": "BLS (placeholder)",
    }


def fetch_nfp() -> dict:
    """Fetch latest NFP values (placeholder)."""
    return {
        "period": "2026-01",
        "payroll_change": 165_000,
        "unemployment_rate": 3.8,
        "release_date": date(2026, 2, 7).isoformat(),
        "source": "BLS (placeholder)",
    }
