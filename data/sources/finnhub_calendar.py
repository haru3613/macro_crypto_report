"""Economic Calendar consensus/expected values.

Sources (tried in order):
1. FMP (Financial Modeling Prep) — requires FMP_API_KEY (paid endpoint)
2. Investing.com internal AJAX — free, no key needed
3. Placeholder fallback

The function name `fetch_economic_consensus` is kept unchanged so that all
call-sites continue to work without modification.
"""

import json
import logging
import os
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 15

# ── Event matching rules (shared between sources) ────────────────────────────
# Each rule: (output_key, event_name_keywords, unit_multiplier)
#   - ALL keywords must appear (case-insensitive)
#   - multiplier converts source unit → our internal unit
#   - Core CPI rule MUST come before headline CPI to avoid false match
_MATCH_RULES: list[tuple[str, list[str], float]] = [
    ("cpi_core_yoy_expected",       ["core", "cpi", "yoy"],              1.0),
    ("cpi_headline_yoy_expected",   ["cpi", "yoy"],                      1.0),
    ("nfp_payroll_change_expected", ["nonfarm payrolls"],                 1_000),
    ("pmi_level_expected",          ["ism", "non-manufacturing", "pmi"], 1.0),
]

_FALLBACK_RULES: list[tuple[str, list[str], float]] = [
    ("nfp_payroll_change_expected", ["non-farm", "payrolls"],             1_000),
    ("nfp_payroll_change_expected", ["employment change"],                1_000),
    ("pmi_level_expected",          ["ism", "services"],                  1.0),
    ("pmi_level_expected",          ["ism", "pmi"],                       1.0),
    ("cpi_core_yoy_expected",       ["core", "consumer price", "yoy"],   1.0),
    ("cpi_headline_yoy_expected",   ["consumer price", "yoy"],           1.0),
]

_ALL_RULES = _MATCH_RULES + _FALLBACK_RULES


def _match_event(
    event_name: str,
    rules: list[tuple[str, list[str], float]],
) -> tuple[str, float] | None:
    name_lower = event_name.lower()
    for key, keywords, multiplier in rules:
        if all(kw.lower() in name_lower for kw in keywords):
            return key, multiplier
    return None


def _empty_result() -> dict[str, float | None]:
    return {
        "cpi_headline_yoy_expected": None,
        "cpi_core_yoy_expected": None,
        "nfp_payroll_change_expected": None,
        "pmi_level_expected": None,
        "cpi_release_date": None,
        "nfp_release_date": None,
        "pmi_release_date": None,
        "pmi_level_actual": None,
        "pmi_level_prev": None,
    }


def _empty_consensus(placeholder: bool = True) -> dict:
    return {
        **_empty_result(),
        "source": "unavailable",
        "is_placeholder": placeholder,
        "events_matched": 0,
        "raw_events": [],
    }


# ── Source 1: FMP (Financial Modeling Prep) ───────────────────────────────────
_FMP_BASE = "https://financialmodelingprep.com/stable/economic-calendar"


def _fmp_api_key() -> str:
    return (
        os.getenv("FMP_API_KEY")
        or os.getenv("FINNHUB_API_KEY")  # backwards-compat
        or ""
    ).strip()


def _fetch_from_fmp() -> dict | None:
    """Fetch from FMP. Returns None if no key or on error."""
    api_key = _fmp_api_key()
    if not api_key:
        return None

    today = date.today()
    params = {
        "from": (today - timedelta(days=45)).isoformat(),
        "to": (today + timedelta(days=30)).isoformat(),
        "apikey": api_key,
    }
    url = f"{_FMP_BASE}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "macro-crypto-report/1.0"})

    with urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        events: list[dict] = json.loads(resp.read().decode("utf-8"))

    us_events = [
        e for e in events
        if "united states" in (e.get("event") or "").lower()
        or (e.get("country") or "").upper() == "US"
    ]

    result = _empty_result()
    matched: list[dict] = []
    us_events.sort(key=lambda e: e.get("date", ""), reverse=True)

    for event in us_events:
        event_name = event.get("event", "")
        estimate = event.get("estimate")
        if estimate is None:
            continue

        match = _match_event(event_name, _ALL_RULES)
        if match is None:
            continue

        key, multiplier = match
        if result[key] is not None:
            continue

        value = estimate * multiplier
        result[key] = int(value) if multiplier >= 1000 else round(value, 1)

        event_date = event.get("date")
        if key.startswith("cpi_") and result["cpi_release_date"] is None and event_date:
            result["cpi_release_date"] = event_date
        if key.startswith("nfp_") and result["nfp_release_date"] is None and event_date:
            result["nfp_release_date"] = event_date
        if key == "pmi_level_expected":
            if result["pmi_release_date"] is None and event_date:
                result["pmi_release_date"] = event_date
            actual = event.get("actual")
            previous = event.get("previous")
            if actual is not None:
                result["pmi_level_actual"] = round(actual, 1)
            if previous is not None:
                result["pmi_level_prev"] = round(previous, 1)

        matched.append({
            "key": key, "event": event_name, "estimate": estimate,
            "actual": event.get("actual"), "previous": event.get("previous"),
            "date": event.get("date", ""),
        })

    return {
        **result,
        "source": "FMP",
        "is_placeholder": False,
        "events_matched": len(matched),
        "raw_events": matched,
    }


# ── Source 2: Investing.com AJAX endpoint ─────────────────────────────────────
_INVESTING_URL = (
    "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
)


def _parse_calendar_value(text: str) -> float | None:
    """Parse '3.0%', '256K', '51.5', '-10K' → float (in source units)."""
    if not text:
        return None
    text = text.strip()
    if text in ("", "\xa0", "—", "&nbsp;"):
        return None
    text = text.replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    elif text.endswith("K"):
        text = text[:-1]
        # Value already in thousands — our _MATCH_RULES multiplier handles conversion
    elif text.endswith("M"):
        text = text[:-1]
    elif text.endswith("B"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


class _CalendarHTMLParser(HTMLParser):
    """Parse investing.com calendar HTML rows.

    Expected structure per row:
        <tr class="js-event-item ...">
            <td ...><span title="United States">USD</span></td>
            <td class="left event"><a title="CPI (YoY)" class="event">...</a></td>
            <td class="... act ...">3.0%</td>
            <td class="... fore ...">3.1%</td>
            <td class="... prev ...">2.9%</td>
        </tr>
    """

    def __init__(self):
        super().__init__()
        self.events: list[dict] = []
        self._row: dict = {}
        self._capture: str = ""   # "actual" | "forecast" | "previous"
        self._buf: str = ""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = d.get("class", "")
        classes = cls.split()

        if tag == "tr" and "js-event-item" in cls:
            self._row = {}
            event_dt = d.get("data-event-datetime", "")
            if event_dt:
                self._row["date"] = event_dt.split()[0].replace("/", "-")
        elif tag == "a" and "event" in classes:
            self._row["name"] = d.get("title", "")
        elif tag == "td":
            if "fore" in classes:
                self._capture = "forecast"
                self._buf = ""
            elif "act" in classes:
                self._capture = "actual"
                self._buf = ""
            elif "prev" in classes:
                self._capture = "previous"
                self._buf = ""

    def handle_data(self, data):
        if self._capture:
            self._buf += data

    def handle_endtag(self, tag):
        if tag == "td" and self._capture:
            self._row[self._capture] = _parse_calendar_value(self._buf)
            self._capture = ""
            self._buf = ""
        elif tag == "tr" and self._row.get("name"):
            self.events.append(self._row)
            self._row = {}


def _fetch_from_investing() -> dict | None:
    """Fetch from investing.com's internal AJAX endpoint (free, no key)."""
    today = date.today()
    body = urlencode({
        "country[]": "5",  # United States
        "dateFrom": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
        "dateTo": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
        "timeZone": "8",
        "timeFilter": "timeRemain",
        "currentTab": "custom",
        "submitFilters": "1",
        "limit_from": "0",
    }).encode("utf-8")

    req = Request(
        _INVESTING_URL,
        data=body,
        method="POST",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.investing.com/economic-calendar/",
            "Origin": "https://www.investing.com",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    with urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    html_data = payload.get("data", "")
    if not html_data:
        logger.warning("Investing.com returned empty calendar data")
        return None

    parser = _CalendarHTMLParser()
    parser.feed(html_data)

    if not parser.events:
        logger.warning("Investing.com: no events parsed from HTML")
        return None

    result = _empty_result()
    matched: list[dict] = []

    # Investing.com event names: "CPI (YoY)", "Core CPI (YoY)",
    # "Nonfarm Payrolls", "ISM Non-Manufacturing PMI"
    for event in parser.events:
        event_name = event.get("name", "")
        forecast = event.get("forecast")
        if forecast is None:
            continue

        match = _match_event(event_name, _ALL_RULES)
        if match is None:
            continue

        key, multiplier = match
        if result[key] is not None:
            continue

        value = forecast * multiplier
        result[key] = int(value) if multiplier >= 1000 else round(value, 1)

        event_date = event.get("date")
        if key.startswith("cpi_") and result["cpi_release_date"] is None and event_date:
            result["cpi_release_date"] = event_date
        if key.startswith("nfp_") and result["nfp_release_date"] is None and event_date:
            result["nfp_release_date"] = event_date
        if key == "pmi_level_expected":
            if result["pmi_release_date"] is None and event_date:
                result["pmi_release_date"] = event_date
            actual = event.get("actual")
            previous = event.get("previous")
            if actual is not None:
                result["pmi_level_actual"] = round(actual, 1)
            if previous is not None:
                result["pmi_level_prev"] = round(previous, 1)

        matched.append({
            "key": key, "event": event_name, "estimate": forecast,
            "actual": event.get("actual"), "previous": event.get("previous"),
            "date": event.get("date", ""),
        })

    if not matched:
        return None

    return {
        **result,
        "source": "Investing.com",
        "is_placeholder": False,
        "events_matched": len(matched),
        "raw_events": matched,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_economic_consensus() -> dict:
    """Fetch US economic consensus estimates.

    Tries sources in order: FMP → Investing.com → placeholder.

    Returns:
        {
            "cpi_headline_yoy_expected": 3.0 | None,
            "cpi_core_yoy_expected": 3.3 | None,
            "nfp_payroll_change_expected": 180000 | None,
            "pmi_level_expected": 51.5 | None,
            "source": "FMP" | "Investing.com" | "unavailable",
            "is_placeholder": False,
            "events_matched": 3,
            "raw_events": [...]
        }
    """
    # 1. Try FMP (requires paid key)
    try:
        result = _fetch_from_fmp()
        if result is not None:
            logger.info("Consensus from FMP (%d events)", result["events_matched"])
            return result
    except HTTPError as exc:
        hint = ""
        if exc.code in (401, 402, 403):
            hint = " (economic-calendar requires paid FMP plan)"
        logger.warning("FMP fetch failed: HTTP %s %s%s", exc.code, exc.reason, hint)
    except Exception as exc:
        logger.warning("FMP fetch failed: %s", exc)

    # 2. Try Investing.com (free, no key)
    try:
        result = _fetch_from_investing()
        if result is not None:
            logger.info(
                "Consensus from Investing.com (%d events)", result["events_matched"]
            )
            return result
    except Exception as exc:
        logger.warning("Investing.com fetch failed: %s", exc)

    # 3. Fallback
    logger.info("No consensus source available, using placeholder")
    return _empty_consensus(placeholder=True)
