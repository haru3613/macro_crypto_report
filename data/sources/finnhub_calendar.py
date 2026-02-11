"""Finnhub Economic Calendar — consensus/expected values for US macro indicators.

Free API (30 calls/sec). Provides estimate (consensus forecast), actual, and
previous values for CPI, NFP, ISM PMI, etc.

Endpoint: GET https://finnhub.io/api/v1/calendar/economic
Docs: https://finnhub.io/docs/api/economic-calendar
"""

import json
import logging
import os
from datetime import date, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_FINNHUB_BASE = "https://finnhub.io/api/v1/calendar/economic"
_REQUEST_TIMEOUT = 12

# ── Event matching rules ──────────────────────────────────────────────────────
# Each rule: (output_key, event_name_keywords, unit_multiplier)
#   - event_name_keywords: ALL must appear in the event name (case-insensitive)
#   - unit_multiplier: multiply the estimate by this to match our internal unit
_MATCH_RULES: list[tuple[str, list[str], float]] = [
    ("cpi_core_yoy_expected",     ["core", "cpi", "yoy"],            1.0),
    ("cpi_headline_yoy_expected", ["cpi", "yoy"],                    1.0),
    ("nfp_payroll_change_expected", ["nonfarm payrolls"],             1_000),  # Finnhub: K → we use raw
    ("pmi_level_expected",        ["ism", "non-manufacturing", "pmi"], 1.0),
]

# Fallback patterns (Finnhub event names vary across months)
_FALLBACK_RULES: list[tuple[str, list[str], float]] = [
    ("nfp_payroll_change_expected", ["non-farm", "payrolls"],         1_000),
    ("nfp_payroll_change_expected", ["employment change"],            1_000),
    ("pmi_level_expected",          ["ism", "services"],              1.0),
    ("pmi_level_expected",          ["ism", "pmi"],                   1.0),
    ("cpi_core_yoy_expected",       ["core", "consumer price", "yoy"], 1.0),
    ("cpi_headline_yoy_expected",   ["consumer price", "yoy"],       1.0),
]


def _finnhub_api_key() -> str:
    # Accept both names for compatibility with different deployment conventions.
    return (os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN") or "").strip()


def _match_event(event_name: str, rules: list[tuple[str, list[str], float]]) -> tuple[str, float] | None:
    """Try to match an event name against rules. Returns (key, multiplier) or None."""
    name_lower = event_name.lower()
    for key, keywords, multiplier in rules:
        if all(kw.lower() in name_lower for kw in keywords):
            return key, multiplier
    return None


def fetch_economic_consensus() -> dict:
    """Fetch US economic calendar from Finnhub and extract consensus estimates.

    Returns:
        {
            "cpi_headline_yoy_expected": 3.0 | None,
            "cpi_core_yoy_expected": 3.3 | None,
            "nfp_payroll_change_expected": 180000 | None,
            "pmi_level_expected": 51.5 | None,
            "source": "Finnhub",
            "is_placeholder": False,
            "events_matched": 3,
            "raw_events": [...]       # matched events for debugging
        }
    """
    api_key = _finnhub_api_key()
    if not api_key:
        logger.info("FINNHUB_API_KEY not set, consensus estimates unavailable")
        return _empty_consensus(placeholder=True)

    try:
        # Look back 45 days and forward 30 days to catch the latest releases
        today = date.today()
        from_date = (today - timedelta(days=45)).isoformat()
        to_date = (today + timedelta(days=30)).isoformat()

        # Finnhub auth is query-param based in official docs (`token=...`).
        params = {"from": from_date, "to": to_date, "token": api_key}
        url = f"{_FINNHUB_BASE}?{urlencode(params)}"
        req = Request(url, headers={
            "Authorization": f"Bearer {api_key}",
            "X-Finnhub-Token": api_key,
            "User-Agent": "macro-crypto-report/1.0",
        })

        with urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        events = data.get("economicCalendar", [])

        # Filter US only
        us_events = [e for e in events if (e.get("country") or "").upper() == "US"]

        result: dict[str, float | None] = {
            "cpi_headline_yoy_expected": None,
            "cpi_core_yoy_expected": None,
            "nfp_payroll_change_expected": None,
            "pmi_level_expected": None,
        }
        matched_events: list[dict] = []

        # Sort by time descending — prefer the most recent release
        us_events.sort(key=lambda e: e.get("time", ""), reverse=True)

        all_rules = _MATCH_RULES + _FALLBACK_RULES

        for event in us_events:
            event_name = event.get("event", "")
            estimate = event.get("estimate")

            if estimate is None:
                continue

            match = _match_event(event_name, all_rules)
            if match is None:
                continue

            key, multiplier = match
            # Only fill if not yet matched (first match = most recent)
            if result[key] is None:
                value = estimate * multiplier
                # Round appropriately
                if multiplier >= 1000:
                    result[key] = int(value)
                else:
                    result[key] = round(value, 1)
                matched_events.append({
                    "key": key,
                    "event": event_name,
                    "estimate": estimate,
                    "actual": event.get("actual"),
                    "prev": event.get("prev"),
                    "time": event.get("time", ""),
                })

        return {
            **result,
            "source": "Finnhub",
            "is_placeholder": False,
            "events_matched": len(matched_events),
            "raw_events": matched_events,
        }

    except HTTPError as exc:
        hint = ""
        if exc.code == 401:
            hint = " (check FINNHUB_API_KEY/FINNHUB_TOKEN value and plan entitlements)"
        logger.warning("Finnhub calendar fetch failed: HTTP %s %s%s", exc.code, exc.reason, hint)
        return _empty_consensus(placeholder=True)
    except Exception as exc:
        logger.warning("Finnhub calendar fetch failed: %s", exc)
        return _empty_consensus(placeholder=True)


def _empty_consensus(placeholder: bool = True) -> dict:
    return {
        "cpi_headline_yoy_expected": None,
        "cpi_core_yoy_expected": None,
        "nfp_payroll_change_expected": None,
        "pmi_level_expected": None,
        "source": "Finnhub (unavailable)" if placeholder else "Finnhub",
        "is_placeholder": placeholder,
        "events_matched": 0,
        "raw_events": [],
    }
