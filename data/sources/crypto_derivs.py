"""Crypto derivatives data source."""

from datetime import date


def fetch_crypto_derivatives() -> dict:
    return {
        "as_of": date(2026, 2, 9).isoformat(),
        "funding_rate": 0.012,
        "open_interest": 21_500_000_000,
        "open_interest_change_7d": -0.03,
        "source": "Coinglass/CryptoQuant (placeholder)",
    }
