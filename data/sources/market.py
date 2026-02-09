"""Market data sources for symbols and OHLCV."""

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
DEFAULT_EXCLUDED_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_top_symbols_vs_usdt(limit: int = 10) -> dict:
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false",
    }
    url = f"{COINGECKO_MARKETS_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as response:
            coins = json.loads(response.read().decode("utf-8"))
    except Exception:
        return {
            "as_of": utc_now_iso(),
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "source": "coingecko_fallback",
            "degraded_reason": "coingecko_unavailable",
        }

    symbols: list[str] = []
    for coin in coins:
        symbol = str(coin.get("symbol", "")).upper()
        if not symbol or symbol in DEFAULT_EXCLUDED_SYMBOLS:
            continue
        pair = f"{symbol}USDT"
        if pair not in symbols:
            symbols.append(pair)
        if len(symbols) >= max(limit + 2, 12):
            break

    # Ensure BTC/ETH are always included.
    for base in ("BTCUSDT", "ETHUSDT"):
        if base not in symbols:
            symbols.insert(0, base)

    # BTC/ETH + top N
    deduped: list[str] = []
    for symbol in symbols:
        if symbol not in deduped:
            deduped.append(symbol)
    final_symbols = deduped[: limit + 2]

    return {
        "as_of": utc_now_iso(),
        "symbols": final_symbols,
        "source": "coingecko",
        "degraded_reason": "",
    }


def fetch_binance_klines(symbol: str, interval: str, limit: int) -> dict:
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    url = f"{BINANCE_KLINES_URL}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
        candles = [
            {
                "open_time": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "close_time": int(row[6]),
            }
            for row in raw
        ]
        return {
            "as_of": utc_now_iso(),
            "symbol": symbol,
            "interval": interval,
            "candles": candles,
            "source": "binance",
            "degraded_reason": "",
        }
    except Exception:
        return {
            "as_of": utc_now_iso(),
            "symbol": symbol,
            "interval": interval,
            "candles": [],
            "source": "binance_fallback",
            "degraded_reason": "binance_unavailable",
        }
