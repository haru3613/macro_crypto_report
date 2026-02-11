from app.config import Settings
from conftest import make_candles, make_sample_context
from services.signal_service import SignalService


def test_signal_service_refresh_and_read(monkeypatch, tmp_path):
    monkeypatch.setattr("services.signal_service.fetch_all_sources", lambda: object())
    monkeypatch.setattr("services.signal_service.compute_report_context", lambda _: make_sample_context())
    monkeypatch.setattr(
        "services.signal_service.fetch_top_symbols_vs_usdt",
        lambda limit=10: {
            "as_of": "2026-02-09T00:00:00+00:00",
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "source": "mock",
            "degraded_reason": "",
        },
    )

    def fake_klines(symbol: str, interval: str, limit: int):
        return {
            "as_of": "2026-02-09T00:00:00+00:00",
            "symbol": symbol,
            "interval": interval,
            "candles": make_candles(120 if interval == "15m" else 260, start=100.0, step=0.8),
            "source": "mock",
            "degraded_reason": "",
        }

    monkeypatch.setattr("services.signal_service.fetch_binance_klines", fake_klines)

    service = SignalService(
        settings=Settings(sqlite_path=str(tmp_path / "signals.db"), short_refresh_minutes=1, long_refresh_hours=1)
    )
    service.refresh(force=True)

    latest = service.latest_signals()
    assert latest
    assert any(s["timeframe"] == "15m" for s in latest)
    assert any(s["timeframe"] == "1d" for s in latest)
    assert service.current_regime()["macro_regime"] in {"risk_off_bias", "neutral", "risk_on_bias"}
