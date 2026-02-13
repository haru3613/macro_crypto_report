"""Stablecoin supply data source via DefiLlama API."""

import json
import logging
from datetime import datetime, timezone
from urllib.request import urlopen

logger = logging.getLogger(__name__)

# Historical total stablecoin supply (all chains, all stablecoins)
DEFILLAMA_CHARTS_URL = "https://stablecoins.llama.fi/stablecoincharts/all"


def fetch_stablecoin_flows() -> dict | None:
    """Fetch aggregate stablecoin market cap and supply delta from DefiLlama.

    Uses /stablecoincharts/all for historical supply data and computes
    1d and 7d deltas from the time series.

    Returns None when data is unavailable.
    """
    try:
        with urlopen(DEFILLAMA_CHARTS_URL, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if len(data) < 8:
            raise ValueError(f"Insufficient data points: {len(data)}")

        def _get_usd(entry: dict) -> float:
            return entry.get("totalCirculatingUSD", {}).get("peggedUSD", 0.0)

        latest = _get_usd(data[-1])
        prev_1d = _get_usd(data[-2])
        prev_7d = _get_usd(data[-8])

        net_flow_24h = round(latest - prev_1d)
        net_flow_7d = round(latest - prev_7d)

        as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "as_of": as_of,
            "net_flow_24h": net_flow_24h,
            "net_flow_7d": net_flow_7d,
            "total_mcap": round(latest),
            "source": "DefiLlama (stablecoincharts/all)",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("DefiLlama stablecoin fetch failed: %s", exc)
        return None
