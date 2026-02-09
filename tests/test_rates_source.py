from data.sources.rates import _fetch_latest_fred_rate


class _FakeResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_fetch_latest_fred_rate_uses_latest_non_empty(monkeypatch):
    csv_payload = "DATE,DGS10\n2026-02-06,4.10\n2026-02-07,.\n2026-02-08,4.20\n"

    def fake_urlopen(_url, timeout=10):
        assert timeout == 10
        return _FakeResponse(csv_payload)

    monkeypatch.setattr("data.sources.rates.urlopen", fake_urlopen)

    as_of, value = _fetch_latest_fred_rate("ignored", "DGS10")
    assert as_of == "2026-02-08"
    assert value == 4.2
