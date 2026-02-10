"""ISM PMI data source via FRED API."""

import json
import logging
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_ism_services_pmi() -> dict:
    """Fetch ISM Manufacturing PMI from FRED (series: NAPM)."""
    try:
        api_key = os.getenv("FRED_API_KEY", "")
        if not api_key:
            raise ValueError("FRED_API_KEY not set")
        params = {
            "series_id": "NAPM",
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }
        url = f"{FRED_API_URL}?{urlencode(params)}"
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        obs = data["observations"][0]
        return {
            "period": obs["date"][:7],
            "headline": float(obs["value"]),
            "release_date": obs["date"],
            "source": "FRED",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("FRED ISM PMI fetch failed, using placeholder: %s", exc)
        return {
            "period": "2026-01",
            "headline": 52.4,
            "release_date": date(2026, 2, 3).isoformat(),
            "source": "ISM (placeholder)",
            "is_placeholder": True,
        }
