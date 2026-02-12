"""Stablecoin supply data source via DefiLlama API."""

import json
import logging
from datetime import date, datetime, timezone
from urllib.request import urlopen

logger = logging.getLogger(__name__)

DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"


def fetch_stablecoin_flows() -> dict:
    """Fetch aggregate stablecoin market cap and supply delta proxy from DefiLlama."""
    try:
        with urlopen(DEFILLAMA_STABLECOINS_URL, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        total_mcap = 0.0
        total_1d_change = 0.0
        total_7d_change = 0.0

        for asset in data.get("peggedAssets", []):
            chains = asset.get("chainCirculating", {})
            current = 0.0
            for chain_data in chains.values():
                current += chain_data.get("current", {}).get("peggedUSD", 0.0)
            total_mcap += current

            mcap_change = asset.get("mcapChange", {})
            total_1d_change += mcap_change.get("1d", 0.0) or 0.0
            total_7d_change += mcap_change.get("7d", 0.0) or 0.0

        as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "as_of": as_of,
            "net_flow_24h": round(total_1d_change),
            "net_flow_7d": round(total_7d_change),
            "total_mcap": round(total_mcap),
            "source": "DefiLlama (stablecoin supply delta proxy)",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("DefiLlama stablecoin fetch failed, using placeholder: %s", exc)
        return {
            "as_of": date.today().isoformat(),
            "net_flow_24h": -250_000_000,
            "net_flow_7d": 1_200_000_000,
            "total_mcap": 0,
            "source": "DefiLlama (placeholder)",
            "is_placeholder": True,
        }
