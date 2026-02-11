"""Tests for the Finnhub economic calendar data source."""

from unittest.mock import patch
import json

from data.sources.finnhub_calendar import fetch_economic_consensus


_FAKE_CALENDAR = {
    "economicCalendar": [
        {
            "country": "US",
            "event": "CPI YoY",
            "estimate": 3.0,
            "actual": 3.1,
            "prev": 2.9,
            "impact": "high",
            "time": "2026-02-13 13:30:00",
            "unit": "%",
        },
        {
            "country": "US",
            "event": "Core CPI YoY",
            "estimate": 3.2,
            "actual": 3.3,
            "prev": 3.1,
            "impact": "high",
            "time": "2026-02-13 13:30:00",
            "unit": "%",
        },
        {
            "country": "US",
            "event": "Nonfarm Payrolls",
            "estimate": 180,
            "actual": 165,
            "prev": 220,
            "impact": "high",
            "time": "2026-02-07 13:30:00",
            "unit": "K",
        },
        {
            "country": "US",
            "event": "ISM Non-Manufacturing PMI",
            "estimate": 51.5,
            "actual": 52.4,
            "prev": 54.1,
            "impact": "medium",
            "time": "2026-02-03 15:00:00",
            "unit": "",
        },
        {
            "country": "DE",  # Not US — should be filtered out
            "event": "CPI YoY",
            "estimate": 2.5,
            "actual": 2.6,
            "prev": 2.4,
            "impact": "high",
            "time": "2026-02-14 07:00:00",
            "unit": "%",
        },
    ],
}


def _fake_urlopen(req, timeout=10):
    class FakeResp:
        def read(self):
            return json.dumps(_FAKE_CALENDAR).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    return FakeResp()


def test_consensus_extracts_cpi(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_urlopen):
        result = fetch_economic_consensus()
    assert result["cpi_headline_yoy_expected"] == 3.0
    assert result["cpi_core_yoy_expected"] == 3.2


def test_consensus_extracts_nfp_in_raw_units(monkeypatch):
    """Finnhub reports NFP in thousands; we store raw (×1000)."""
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_urlopen):
        result = fetch_economic_consensus()
    assert result["nfp_payroll_change_expected"] == 180_000


def test_consensus_extracts_pmi(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_urlopen):
        result = fetch_economic_consensus()
    assert result["pmi_level_expected"] == 51.5


def test_consensus_filters_non_us(monkeypatch):
    """German CPI should not appear in results."""
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    with patch("data.sources.finnhub_calendar.urlopen", _fake_urlopen):
        result = fetch_economic_consensus()
    # Only 4 US events matched
    assert result["events_matched"] == 4
    assert result["is_placeholder"] is False


def test_consensus_without_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    result = fetch_economic_consensus()
    assert result["is_placeholder"] is True
    assert result["cpi_headline_yoy_expected"] is None
    assert result["nfp_payroll_change_expected"] is None


def test_consensus_fallback_on_error(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    def bad_urlopen(req, timeout=10):
        raise ConnectionError("network error")
    with patch("data.sources.finnhub_calendar.urlopen", bad_urlopen):
        result = fetch_economic_consensus()
    assert result["is_placeholder"] is True


def test_consensus_handles_missing_estimate(monkeypatch):
    """Events without estimate field should be skipped."""
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    calendar = {
        "economicCalendar": [
            {
                "country": "US",
                "event": "CPI YoY",
                "estimate": None,
                "actual": None,
                "prev": 2.9,
                "time": "2026-03-13 13:30:00",
            },
        ],
    }
    def fake(req, timeout=10):
        class R:
            def read(self): return json.dumps(calendar).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()
    with patch("data.sources.finnhub_calendar.urlopen", fake):
        result = fetch_economic_consensus()
    assert result["cpi_headline_yoy_expected"] is None
