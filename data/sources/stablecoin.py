"""Stablecoin flow data source."""

from datetime import date


def fetch_stablecoin_flows() -> dict:
    return {
        "as_of": date(2026, 2, 9).isoformat(),
        "net_flow_24h": -250_000_000,
        "net_flow_7d": 1_200_000_000,
        "source": "CryptoQuant (placeholder)",
    }
