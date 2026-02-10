"""BLS macro data sources (CPI, NFP) via FRED API."""

import json
import logging
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


def _fred_api_key() -> str:
    return os.getenv("FRED_API_KEY", "")


def _fetch_fred_series(series_id: str, limit: int = 2) -> list[dict]:
    """Fetch recent observations from a FRED series."""
    api_key = _fred_api_key()
    if not api_key:
        raise ValueError("FRED_API_KEY not set")
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    url = f"{FRED_API_URL}?{urlencode(params)}"
    with urlopen(url, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("observations", [])


def fetch_cpi() -> dict:
    """Fetch latest CPI values from FRED (CPIAUCSL headline, CPILFESL core)."""
    try:
        headline_obs = _fetch_fred_series("CPIAUCSL", limit=13)
        core_obs = _fetch_fred_series("CPILFESL", limit=13)

        # YoY: compare latest to 12 months ago
        h_latest = float(headline_obs[0]["value"])
        h_year_ago = float(headline_obs[12]["value"])
        headline_yoy = round((h_latest - h_year_ago) / h_year_ago * 100, 1)

        c_latest = float(core_obs[0]["value"])
        c_year_ago = float(core_obs[12]["value"])
        core_yoy = round((c_latest - c_year_ago) / c_year_ago * 100, 1)

        period = headline_obs[0]["date"][:7]  # "YYYY-MM"
        return {
            "period": period,
            "headline_yoy": headline_yoy,
            "core_yoy": core_yoy,
            "release_date": headline_obs[0]["date"],
            "source": "FRED",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("FRED CPI fetch failed, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "headline_yoy": 3.1,
            "core_yoy": 3.3,
            "release_date": date(2026, 2, 13).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }


def fetch_nfp() -> dict:
    """Fetch latest NFP values from FRED (PAYEMS payrolls, UNRATE unemployment)."""
    try:
        payroll_obs = _fetch_fred_series("PAYEMS", limit=2)
        unrate_obs = _fetch_fred_series("UNRATE", limit=1)

        latest = float(payroll_obs[0]["value"])
        previous = float(payroll_obs[1]["value"])
        payroll_change = int((latest - previous) * 1000)  # PAYEMS is in thousands

        unemployment_rate = float(unrate_obs[0]["value"])
        period = payroll_obs[0]["date"][:7]
        return {
            "period": period,
            "payroll_change": payroll_change,
            "unemployment_rate": unemployment_rate,
            "release_date": payroll_obs[0]["date"],
            "source": "FRED",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("FRED NFP fetch failed, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "payroll_change": 165_000,
            "unemployment_rate": 3.8,
            "release_date": date(2026, 2, 7).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }
