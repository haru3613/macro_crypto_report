from conftest import FakeResponse
from data.sources.rates import _fetch_latest_fred_rate


def test_fetch_latest_fred_rate_uses_latest_non_empty(monkeypatch):
    csv_payload = "DATE,DGS10\n2026-02-06,4.10\n2026-02-07,.\n2026-02-08,4.20\n"

    def fake_urlopen(_url, timeout=10):
        assert timeout == 10
        return FakeResponse(csv_payload)

    monkeypatch.setattr("data.sources.rates.urlopen", fake_urlopen)

    as_of, value = _fetch_latest_fred_rate("ignored", "DGS10")
    assert as_of == "2026-02-08"
    assert value == 4.2


def test_fetch_latest_fred_rate_observation_date_format(monkeypatch):
    """FRED CSV now uses 'observation_date' instead of 'DATE'."""
    csv_payload = "observation_date,DGS10\n2026-02-06,4.10\n2026-02-07,.\n2026-02-08,4.25\n"

    def fake_urlopen(_url, timeout=10):
        return FakeResponse(csv_payload)

    monkeypatch.setattr("data.sources.rates.urlopen", fake_urlopen)

    as_of, value = _fetch_latest_fred_rate("ignored", "DGS10")
    assert as_of == "2026-02-08"
    assert value == 4.25
