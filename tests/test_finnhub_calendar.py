"""Tests for the economic calendar consensus data source (FMP + Investing.com)."""

from unittest.mock import patch
import json

from data.sources.finnhub_calendar import (
    fetch_economic_consensus,
    _parse_calendar_value,
    _CalendarHTMLParser,
)


# ── FMP test data ────────────────────────────────────────────────────────────

_FAKE_FMP_DATA = [
    {
        "country": "US",
        "event": "United States CPI YoY",
        "estimate": 3.0,
        "actual": 3.1,
        "previous": 2.9,
        "date": "2026-02-13",
    },
    {
        "country": "US",
        "event": "United States Core CPI YoY",
        "estimate": 3.2,
        "actual": 3.3,
        "previous": 3.1,
        "date": "2026-02-13",
    },
    {
        "country": "US",
        "event": "United States Nonfarm Payrolls",
        "estimate": 180,
        "actual": 165,
        "previous": 220,
        "date": "2026-02-07",
    },
    {
        "country": "US",
        "event": "United States ISM Non-Manufacturing PMI",
        "estimate": 51.5,
        "actual": 52.4,
        "previous": 54.1,
        "date": "2026-02-03",
    },
    {
        "country": "DE",
        "event": "Germany CPI YoY",
        "estimate": 2.5,
        "actual": 2.6,
        "previous": 2.4,
        "date": "2026-02-14",
    },
]


def _fake_fmp_urlopen(req, timeout=10):
    class FakeResp:
        def read(self):
            return json.dumps(_FAKE_FMP_DATA).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    return FakeResp()


# ── Investing.com test data ──────────────────────────────────────────────────

_FAKE_INVESTING_HTML = """
<tr id="eventRowId_100" class="js-event-item" data-event-datetime="2026/02/13 08:30:00">
  <td class="flagCur noWrap"><span title="United States">USD</span></td>
  <td class="left textNum sentiment noWrap"><span class="three" title="3"></span></td>
  <td class="left event"><a href="/economic-calendar/cpi-yoy-733" class="event" title="CPI (YoY)">CPI (YoY)</a></td>
  <td class="bold act">3.1%</td>
  <td class="fore">3.0%</td>
  <td class="prev">2.9%</td>
</tr>
<tr id="eventRowId_101" class="js-event-item" data-event-datetime="2026/02/13 08:30:00">
  <td class="flagCur noWrap"><span title="United States">USD</span></td>
  <td class="left textNum sentiment noWrap"><span class="three" title="3"></span></td>
  <td class="left event"><a href="/economic-calendar/core-cpi-yoy-736" class="event" title="Core CPI (YoY)">Core CPI (YoY)</a></td>
  <td class="bold act">3.3%</td>
  <td class="fore">3.2%</td>
  <td class="prev">3.1%</td>
</tr>
<tr id="eventRowId_102" class="js-event-item" data-event-datetime="2026/02/07 08:30:00">
  <td class="flagCur noWrap"><span title="United States">USD</span></td>
  <td class="left textNum sentiment noWrap"><span class="three" title="3"></span></td>
  <td class="left event"><a href="/economic-calendar/nonfarm-payrolls-227" class="event" title="Nonfarm Payrolls">Nonfarm Payrolls</a></td>
  <td class="bold act">165K</td>
  <td class="fore">180K</td>
  <td class="prev">220K</td>
</tr>
<tr id="eventRowId_103" class="js-event-item" data-event-datetime="2026/02/03 10:00:00">
  <td class="flagCur noWrap"><span title="United States">USD</span></td>
  <td class="left textNum sentiment noWrap"><span class="two" title="2"></span></td>
  <td class="left event"><a href="/economic-calendar/ism-non-manufacturing-pmi-176" class="event" title="ISM Non-Manufacturing PMI">ISM Non-Manufacturing PMI</a></td>
  <td class="bold act">52.4</td>
  <td class="fore">51.5</td>
  <td class="prev">54.1</td>
</tr>
"""


def _fake_investing_urlopen(req, timeout=10):
    class FakeResp:
        def read(self):
            return json.dumps({"data": _FAKE_INVESTING_HTML}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    return FakeResp()


# ── FMP source tests ─────────────────────────────────────────────────────────

def test_fmp_extracts_cpi(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_fmp_urlopen):
        result = fetch_economic_consensus()
    assert result["cpi_headline_yoy_expected"] == 3.0
    assert result["cpi_core_yoy_expected"] == 3.2
    assert result["source"] == "FMP"


def test_fmp_extracts_nfp_in_raw_units(monkeypatch):
    """FMP reports NFP in thousands; we store raw (x1000)."""
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_fmp_urlopen):
        result = fetch_economic_consensus()
    assert result["nfp_payroll_change_expected"] == 180_000


def test_fmp_extracts_pmi(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_fmp_urlopen):
        result = fetch_economic_consensus()
    assert result["pmi_level_expected"] == 51.5


def test_fmp_filters_non_us(monkeypatch):
    """German CPI should not appear in results."""
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_fmp_urlopen):
        result = fetch_economic_consensus()
    assert result["events_matched"] == 4
    assert result["is_placeholder"] is False


# ── Investing.com source tests ───────────────────────────────────────────────

def test_investing_extracts_cpi(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with patch("data.sources.finnhub_calendar.urlopen", _fake_investing_urlopen):
        result = fetch_economic_consensus()
    assert result["cpi_headline_yoy_expected"] == 3.0
    assert result["cpi_core_yoy_expected"] == 3.2
    assert result["source"] == "Investing.com"


def test_investing_extracts_nfp(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with patch("data.sources.finnhub_calendar.urlopen", _fake_investing_urlopen):
        result = fetch_economic_consensus()
    assert result["nfp_payroll_change_expected"] == 180_000


def test_investing_extracts_pmi(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with patch("data.sources.finnhub_calendar.urlopen", _fake_investing_urlopen):
        result = fetch_economic_consensus()
    assert result["pmi_level_expected"] == 51.5
    assert result["events_matched"] == 4


# ── HTML parser unit tests ───────────────────────────────────────────────────

def test_parse_calendar_value_percent():
    assert _parse_calendar_value("3.0%") == 3.0
    assert _parse_calendar_value("-0.5%") == -0.5


def test_parse_calendar_value_k_suffix():
    assert _parse_calendar_value("256K") == 256.0
    assert _parse_calendar_value("-10K") == -10.0


def test_parse_calendar_value_empty():
    assert _parse_calendar_value("") is None
    assert _parse_calendar_value("—") is None
    assert _parse_calendar_value("\xa0") is None


def test_html_parser_extracts_events():
    parser = _CalendarHTMLParser()
    parser.feed(_FAKE_INVESTING_HTML)
    assert len(parser.events) == 4
    names = [e["name"] for e in parser.events]
    assert "CPI (YoY)" in names
    assert "Nonfarm Payrolls" in names


# ── Fallback tests ───────────────────────────────────────────────────────────

def test_consensus_without_api_key(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    # Investing.com also fails → placeholder
    def bad_urlopen(req, timeout=10):
        raise ConnectionError("network error")
    with patch("data.sources.finnhub_calendar.urlopen", bad_urlopen):
        result = fetch_economic_consensus()
    assert result["is_placeholder"] is True
    assert result["cpi_headline_yoy_expected"] is None
    assert result["nfp_payroll_change_expected"] is None


def test_consensus_fallback_on_error(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    def bad_urlopen(req, timeout=10):
        raise ConnectionError("network error")
    with patch("data.sources.finnhub_calendar.urlopen", bad_urlopen):
        result = fetch_economic_consensus()
    assert result["is_placeholder"] is True


def test_consensus_handles_missing_estimate(monkeypatch):
    """Events without estimate field should be skipped."""
    monkeypatch.setenv("FMP_API_KEY", "test-key")
    calendar = [
        {
            "country": "US",
            "event": "United States CPI YoY",
            "estimate": None,
            "actual": None,
            "previous": 2.9,
            "date": "2026-03-13",
        },
    ]
    def fake(req, timeout=10):
        class R:
            def read(self): return json.dumps(calendar).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()
    with patch("data.sources.finnhub_calendar.urlopen", fake):
        result = fetch_economic_consensus()
    assert result["cpi_headline_yoy_expected"] is None
