"""CME BTC futures OHLC source."""

from datetime import date


def fetch_cme_ohlc() -> list[dict]:
    return [
        {
            "date": date(2026, 2, 6).isoformat(),
            "open": 43_500,
            "high": 44_200,
            "low": 42_900,
            "close": 43_900,
        },
        {
            "date": date(2026, 2, 9).isoformat(),
            "open": 44_050,
            "high": 44_800,
            "low": 43_600,
            "close": 44_500,
        },
    ]
