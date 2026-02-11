"""Market data sources for symbols and OHLCV."""

import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
DEFAULT_EXCLUDED_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE"}

# Cached set of valid Binance USDT pairs
_binance_usdt_pairs: set[str] | None = None


def _get_binance_usdt_pairs() -> set[str]:
    """Fetch and cache the set of valid USDT trading pairs from Binance."""
    global _binance_usdt_pairs
    if _binance_usdt_pairs is not None:
        return _binance_usdt_pairs
    try:
        with urlopen(f"{BINANCE_EXCHANGE_INFO_URL}?permissions=SPOT", timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        _binance_usdt_pairs = {
            s["symbol"] for s in data.get("symbols", [])
            if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"
        }
    except Exception as exc:
        logger.warning("Binance exchangeInfo fetch failed: %s", exc)
        _binance_usdt_pairs = set()
    return _binance_usdt_pairs


def utc_now_iso() -> str:
    # Canonical version lives in signals.schema; keep a local alias to
    # avoid a cross-layer import from data -> signals.
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
    except Exception as exc:
        logger.warning("CoinGecko fetch failed, using fallback: %s", exc)
        return {
            "as_of": utc_now_iso(),
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "source": "coingecko_fallback",
            "degraded_reason": "coingecko_unavailable",
            "is_placeholder": True,
        }

    valid_pairs = _get_binance_usdt_pairs()
    symbols: list[str] = []
    for coin in coins:
        symbol = str(coin.get("symbol", "")).upper()
        if not symbol or symbol in DEFAULT_EXCLUDED_SYMBOLS:
            continue
        if not symbol.isalnum():
            continue
        pair = f"{symbol}USDT"
        # Only include pairs that actually exist on Binance
        if valid_pairs and pair not in valid_pairs:
            continue
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
        "is_placeholder": False,
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
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("Binance klines fetch failed for %s/%s: %s", symbol, interval, exc)
        return {
            "as_of": utc_now_iso(),
            "symbol": symbol,
            "interval": interval,
            "candles": [],
            "source": "binance_fallback",
            "degraded_reason": "binance_unavailable",
            "is_placeholder": True,
        }
