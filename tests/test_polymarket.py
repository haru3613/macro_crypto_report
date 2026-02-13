"""Tests for the Polymarket data source."""

from unittest.mock import patch
import json

from data.sources.polymarket import fetch_polymarket_macro


_FAKE_MARKETS = [
    {
        "question": "Will February CPI YoY exceed 3.0%?",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.35", "0.65"],
        "volume": "95000",
        "endDate": "2026-03-12T00:00:00Z",
        "slug": "cpi-above-3-feb",
        "tags": [{"label": "CPI"}],
        "active": True,
        "closed": False,
    },
    {
        "question": "Will NFP exceed 200k in January 2026?",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.42", "0.58"],
        "volume": "60000",
        "endDate": "2026-02-10T00:00:00Z",
        "slug": "nfp-above-200k-jan",
        "tags": [{"label": "NFP"}],
        "active": True,
        "closed": False,
    },
    {
        "question": "Will stocks go up tomorrow?",   # not macro — should be filtered
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.5", "0.5"],
        "volume": "10000",
        "endDate": "2026-02-12T00:00:00Z",
        "slug": "stocks-up",
        "tags": [],
        "active": True,
        "closed": False,
    },
]


def _fake_urlopen(url, timeout=10):
    class FakeResp:
        def read(self):
            return json.dumps(_FAKE_MARKETS).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    return FakeResp()


def test_fetch_polymarket_macro_filters_keywords():
    with patch("data.sources.polymarket.urlopen", _fake_urlopen):
        result = fetch_polymarket_macro()
    assert result["is_placeholder"] is False
    assert result["source"].startswith("Polymarket")
    questions = [m["question"] for m in result["markets"]]
    assert any("CPI" in q for q in questions)
    assert any("NFP" in q for q in questions)
    # Non-macro market should be excluded
    assert not any("stocks" in q.lower() for q in questions)


def test_fetch_polymarket_macro_outcome_prices():
    with patch("data.sources.polymarket.urlopen", _fake_urlopen):
        result = fetch_polymarket_macro()
    cpi_market = next(m for m in result["markets"] if "CPI" in m["question"])
    assert abs(cpi_market["outcomes"]["Yes"] - 0.35) < 0.001
    assert abs(cpi_market["outcomes"]["No"] - 0.65) < 0.001


def test_fetch_polymarket_macro_returns_none_on_error():
    def bad_urlopen(url, timeout=10):
        raise ConnectionError("network error")
    with patch("data.sources.polymarket.urlopen", bad_urlopen):
        result = fetch_polymarket_macro()
    assert result is None


def test_fetch_polymarket_macro_outcomes_as_json_string():
    """outcomes and outcomePrices returned as JSON strings (not lists)."""
    json_string_markets = [
        {
            "question": "Will February CPI YoY exceed 3.0%?",
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0.35", "0.65"]',
            "volume": "95000",
            "endDate": "2026-03-12T00:00:00Z",
            "slug": "cpi-above-3-feb",
            "tags": [{"label": "CPI"}],
            "active": True,
            "closed": False,
        }
    ]
    def json_str_urlopen(url, timeout=10):
        class R:
            def read(self): return json.dumps(json_string_markets).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()
    with patch("data.sources.polymarket.urlopen", json_str_urlopen):
        result = fetch_polymarket_macro()
    cpi_market = result["markets"][0]
    assert cpi_market["outcomes"]["Yes"] == 0.35
    assert cpi_market["outcomes"]["No"] == 0.65


def test_fetch_polymarket_macro_low_volume_filtered():
    low_vol_markets = [
        {
            "question": "Will CPI exceed 3%?",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.4", "0.6"],
            "volume": "100",           # below _MIN_VOLUME threshold
            "endDate": "2026-03-01T00:00:00Z",
            "slug": "low-vol",
            "tags": [{"label": "CPI"}],
            "active": True,
            "closed": False,
        }
    ]
    def low_vol_urlopen(url, timeout=10):
        class R:
            def read(self): return json.dumps(low_vol_markets).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()
    with patch("data.sources.polymarket.urlopen", low_vol_urlopen):
        result = fetch_polymarket_macro()
    # Returns None because no market exceeds volume threshold
    assert result is None
