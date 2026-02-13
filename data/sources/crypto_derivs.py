"""Crypto derivatives data source via Binance Futures API."""

import json
import logging
from datetime import date, datetime, timezone
from urllib.request import urlopen

logger = logging.getLogger(__name__)

BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
BINANCE_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"
BINANCE_OI_HIST_URL = "https://fapi.binance.com/futures/data/openInterestHist"


def fetch_crypto_derivatives() -> dict | None:
    """Fetch BTC funding rate and open interest from Binance Futures.

    Returns None when data is unavailable.
    """
    try:
        # Funding rate
        with urlopen(f"{BINANCE_FUNDING_URL}?symbol=BTCUSDT&limit=1", timeout=15) as resp:
            funding_data = json.loads(resp.read().decode("utf-8"))
        funding_rate = float(funding_data[0]["fundingRate"])

        # Current open interest
        with urlopen(f"{BINANCE_OI_URL}?symbol=BTCUSDT", timeout=15) as resp:
            oi_data = json.loads(resp.read().decode("utf-8"))
        open_interest = float(oi_data["openInterest"])

        # 7d OI change: fetch 8 days of daily OI history
        with urlopen(f"{BINANCE_OI_HIST_URL}?symbol=BTCUSDT&period=1d&limit=8", timeout=15) as resp:
            oi_hist = json.loads(resp.read().decode("utf-8"))

        if len(oi_hist) >= 2:
            oi_latest = float(oi_hist[-1]["sumOpenInterest"])
            oi_oldest = float(oi_hist[0]["sumOpenInterest"])
            oi_change_7d = round((oi_latest - oi_oldest) / oi_oldest, 4) if oi_oldest > 0 else 0.0
            oi_usd = oi_latest
        else:
            oi_change_7d = 0.0
            oi_usd = open_interest

        as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "as_of": as_of,
            "funding_rate": funding_rate,
            "open_interest": oi_usd,
            "open_interest_change_7d": oi_change_7d,
            "source": "Binance Futures",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("Binance derivatives fetch failed: %s", exc)
        return None
