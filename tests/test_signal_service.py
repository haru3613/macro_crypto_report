from app.config import Settings
from report.schema import ReportContext
from services.signal_service import SignalService


def _sample_context() -> ReportContext:
    return ReportContext(
        as_of="2026-02-09",
        macro_events={
            "cpi_release": "2026-02-13",
            "nfp_release": "2026-02-07",
            "pmi_level": 52.4,
            "pmi_state": "expansion",
            "fomc_next_meeting": "2026-03-18",
            "event_risk_week": True,
        },
        rates={"yield_curve_slope": -0.3, "ten_year": 4.05, "two_year": 4.35},
        fedwatch={"probabilities": {"cut": 0.2, "hold": 0.7, "hike": 0.1}},
        cme_gap={"status": "gap_up", "gap": 120},
        derivatives={},
        stablecoin_flows={},
    )


def _candles(n: int, start: float = 100.0, step: float = 1.0) -> list[dict]:
    rows = []
    px = start
    for idx in range(n):
        px += step
        rows.append(
            {
                "open_time": idx,
                "open": px - 0.3,
                "high": px + 1.0,
                "low": px - 1.0,
                "close": px,
                "volume": 5000 + idx,
                "close_time": idx + 1,
            }
        )
    return rows


def test_signal_service_refresh_and_read(monkeypatch, tmp_path):
    monkeypatch.setattr("services.signal_service.fetch_all_sources", lambda: object())
    monkeypatch.setattr("services.signal_service.compute_report_context", lambda _: _sample_context())
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
            "candles": _candles(120 if interval == "15m" else 260, start=100.0, step=0.8),
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
