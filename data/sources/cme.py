"""CME BTC futures OHLC source (uses Binance daily klines as proxy)."""

import json
import logging
from datetime import date, datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


def fetch_cme_ohlc() -> list[dict] | None:
    """Fetch recent BTC daily OHLC from Binance as a CME proxy.

    Returns None when data is unavailable.
    """
    try:
        params = {"symbol": "BTCUSDT", "interval": "1d", "limit": 3}
        url = f"{BINANCE_KLINES_URL}?{urlencode(params)}"
        with urlopen(url, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))

        candles = []
        for row in raw:
            open_time_ms = int(row[0])
            dt = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
            candles.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "source": "Binance (CME proxy)",
                "is_placeholder": False,
            })
        return candles
    except Exception as exc:
        logger.warning("Binance daily klines fetch failed: %s", exc)
        return None
