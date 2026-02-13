"""Polymarket prediction market data source.

Fetches active macro-related prediction markets (CPI, NFP, PMI, Fed rate)
from the Polymarket Gamma API (public, no auth required).

Returns binary market probabilities as market-implied directional odds.
These are NOT consensus point estimates — always labelled as non-official.

API: https://gamma-api.polymarket.com  (Gamma Markets API)
Rate limit: 300 req/10s for /markets — safe for periodic polling.
"""

import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_GAMMA_BASE = "https://gamma-api.polymarket.com"
_MACRO_KEYWORDS = ("CPI", "inflation", "NFP", "non-farm", "payroll",
                   "unemployment", "PMI", "Fed rate", "FOMC", "interest rate")
_MIN_VOLUME = 5_000        # Ignore markets with < $5k volume (noise)
_MAX_MARKETS = 8           # Cap total returned markets
_REQUEST_TIMEOUT = 12


def _fetch_active_macro_markets() -> list[dict]:
    """Fetch active markets from Gamma API, filtered for macro topics."""
    params = {
        "closed": "false",
        "active": "true",
        "order": "volume",
        "ascending": "false",
        "limit": 200,
    }
    url = f"{_GAMMA_BASE}/markets?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "macro-crypto-report/1.0"})
    with urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        markets: list[dict] = json.loads(resp.read().decode("utf-8"))

    results = []
    for m in markets:
        question = (m.get("question") or "").upper()
        tags = " ".join(t.get("label", "") for t in (m.get("tags") or [])).upper()
        text = question + " " + tags
        if not any(kw.upper() in text for kw in _MACRO_KEYWORDS):
            continue
        volume = float(m.get("volume") or 0)
        if volume < _MIN_VOLUME:
            continue

        outcomes = m.get("outcomes") or []
        prices_raw = m.get("outcomePrices") or []
        # outcomes and outcomePrices may be JSON strings or lists
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except (json.JSONDecodeError, ValueError):
                outcomes = []
        if isinstance(prices_raw, str):
            try:
                prices_raw = json.loads(prices_raw)
            except (json.JSONDecodeError, ValueError):
                prices_raw = []

        prices = []
        for p in prices_raw:
            try:
                prices.append(round(float(p), 3))
            except (TypeError, ValueError):
                prices.append(None)

        outcome_map = {}
        for outcome, price in zip(outcomes, prices):
            outcome_map[outcome] = price

        end_date = m.get("endDate") or m.get("end_date_iso") or ""

        results.append({
            "question": m.get("question", ""),
            "outcomes": outcome_map,       # {"Yes": 0.35, "No": 0.65}
            "volume_usd": int(volume),
            "end_date": end_date[:10] if end_date else "",
            "slug": m.get("slug", ""),
        })

        if len(results) >= _MAX_MARKETS:
            break

    return results


def fetch_polymarket_macro() -> dict | None:
    """Return active macro prediction markets from Polymarket.

    Returns None when data is unavailable.
    """
    try:
        markets = _fetch_active_macro_markets()
        if not markets:
            raise ValueError("No macro markets found above volume threshold")
        return {
            "markets": markets,
            "source": "Polymarket (market-derived, non-official)",
            "is_placeholder": False,
        }
    except Exception as exc:
        logger.warning("Polymarket fetch failed: %s", exc)
        return None
