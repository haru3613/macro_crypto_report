"""BLS macro data sources (CPI, NFP) via FRED API."""

import json
import logging
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


class MissingFredApiKeyError(RuntimeError):
    """Raised when FRED_API_KEY is unavailable."""


def _fred_api_key() -> str:
    return os.getenv("FRED_API_KEY", "")


def _fetch_fred_series(series_id: str, limit: int = 2) -> list[dict]:
    """Fetch recent observations from a FRED series."""
    api_key = _fred_api_key()
    if not api_key:
        raise MissingFredApiKeyError("FRED_API_KEY not set")
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


def _estimate_us_cpi_release_date(period_date: str) -> str:
    """Estimate CPI release date as 2nd Tuesday of following month.

    FRED CPI series date is the reference month (e.g. 2025-12-01), not BLS
    release timestamp. We convert to an estimated publication date used for
    report display.
    """
    year, month, _ = map(int, period_date.split("-"))
    rel_year = year + 1 if month == 12 else year
    rel_month = 1 if month == 12 else month + 1

    first = date(rel_year, rel_month, 1)
    days_to_tuesday = (1 - first.weekday()) % 7  # Monday=0, Tuesday=1
    first_tuesday = 1 + days_to_tuesday
    second_tuesday = first_tuesday + 7
    return date(rel_year, rel_month, second_tuesday).isoformat()


def _estimate_us_nfp_release_date(period_date: str) -> str:
    """Estimate NFP release date as 1st Friday of following month.

    PAYEMS reference date is month-start (e.g. 2026-01-01) and is not the BLS
    publication date.
    """
    year, month, _ = map(int, period_date.split("-"))
    rel_year = year + 1 if month == 12 else year
    rel_month = 1 if month == 12 else month + 1

    first = date(rel_year, rel_month, 1)
    days_to_friday = (4 - first.weekday()) % 7  # Friday=4
    first_friday = 1 + days_to_friday
    return date(rel_year, rel_month, first_friday).isoformat()


def fetch_cpi() -> dict:
    """Fetch latest CPI values from FRED (CPIAUCSL headline, CPILFESL core)."""
    try:
        headline_obs = _fetch_fred_series("CPIAUCSL", limit=14)
        core_obs = _fetch_fred_series("CPILFESL", limit=14)

        # YoY: compare latest to 12 months ago
        h_latest = float(headline_obs[0]["value"])
        h_year_ago = float(headline_obs[12]["value"])
        headline_yoy = round((h_latest - h_year_ago) / h_year_ago * 100, 1)

        h_prev = float(headline_obs[1]["value"])
        h_prev_year_ago = float(headline_obs[13]["value"])
        headline_yoy_prev = round((h_prev - h_prev_year_ago) / h_prev_year_ago * 100, 1)

        c_latest = float(core_obs[0]["value"])
        c_year_ago = float(core_obs[12]["value"])
        core_yoy = round((c_latest - c_year_ago) / c_year_ago * 100, 1)

        c_prev = float(core_obs[1]["value"])
        c_prev_year_ago = float(core_obs[13]["value"])
        core_yoy_prev = round((c_prev - c_prev_year_ago) / c_prev_year_ago * 100, 1)

        period = headline_obs[0]["date"][:7]  # "YYYY-MM"
        period_date = headline_obs[0]["date"]  # reference period (month start)
        return {
            "period": period,
            "period_date": period_date,
            "headline_yoy": headline_yoy,
            "headline_yoy_prev": headline_yoy_prev,
            "headline_yoy_expected": None,
            "core_yoy": core_yoy,
            "core_yoy_prev": core_yoy_prev,
            "core_yoy_expected": None,
            "release_date": _estimate_us_cpi_release_date(period_date),
            "source": "FRED",
            "is_placeholder": False,
        }
    except MissingFredApiKeyError as exc:
        logger.info("FRED CPI unavailable, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "period_date": "2026-01-01",
            "headline_yoy": 3.1,
            "headline_yoy_prev": 2.9,
            "headline_yoy_expected": None,
            "core_yoy": 3.3,
            "core_yoy_prev": 3.2,
            "core_yoy_expected": None,
            "release_date": date(2026, 2, 13).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }
    except Exception as exc:
        logger.warning("FRED CPI fetch failed, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "period_date": "2026-01-01",
            "headline_yoy": 3.1,
            "headline_yoy_prev": 2.9,
            "headline_yoy_expected": None,
            "core_yoy": 3.3,
            "core_yoy_prev": 3.2,
            "core_yoy_expected": None,
            "release_date": date(2026, 2, 13).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }


def fetch_nfp() -> dict:
    """Fetch latest NFP values from FRED (PAYEMS payrolls, UNRATE unemployment)."""
    try:
        payroll_obs = _fetch_fred_series("PAYEMS", limit=3)
        unrate_obs = _fetch_fred_series("UNRATE", limit=2)

        # PAYEMS is in thousands of persons (level); difference = monthly change
        latest = float(payroll_obs[0]["value"])
        prev_month = float(payroll_obs[1]["value"])
        prev_prev_month = float(payroll_obs[2]["value"])
        payroll_change = int((latest - prev_month) * 1000)
        payroll_change_prev = int((prev_month - prev_prev_month) * 1000)

        unemployment_rate = float(unrate_obs[0]["value"])
        unemployment_rate_prev = float(unrate_obs[1]["value"])

        period = payroll_obs[0]["date"][:7]
        period_date = payroll_obs[0]["date"]
        return {
            "period": period,
            "period_date": period_date,
            "payroll_change": payroll_change,
            "payroll_change_prev": payroll_change_prev,
            "payroll_change_expected": None,
            "unemployment_rate": unemployment_rate,
            "unemployment_rate_prev": unemployment_rate_prev,
            "release_date": _estimate_us_nfp_release_date(period_date),
            "source": "FRED",
            "is_placeholder": False,
        }
    except MissingFredApiKeyError as exc:
        logger.info("FRED NFP unavailable, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "period_date": "2026-01-01",
            "payroll_change": 170000,
            "payroll_change_prev": 256000,
            "payroll_change_expected": None,
            "unemployment_rate": 4.1,
            "unemployment_rate_prev": 4.2,
            "release_date": date(2026, 2, 6).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }
    except Exception as exc:
        logger.warning("FRED NFP fetch failed, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "period_date": "2026-01-01",
            "payroll_change": 165_000,
            "payroll_change_prev": 220_000,
            "payroll_change_expected": None,
            "unemployment_rate": 3.8,
            "unemployment_rate_prev": 4.0,
            "release_date": date(2026, 2, 7).isoformat(),
            "source": "BLS (placeholder)",
            "is_placeholder": True,
        }
