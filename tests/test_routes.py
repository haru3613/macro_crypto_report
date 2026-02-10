"""Route-level tests using FastAPI TestClient."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from conftest import make_candles, make_sample_context


def _mock_signal_service_class(tmp_path):
    """Create a SignalService with mocked external dependencies."""
    from app.config import Settings
    from services.signal_service import SignalService

    ctx = make_sample_context()

    with (
        patch("services.signal_service.fetch_all_sources", return_value=object()),
        patch("services.signal_service.compute_report_context", return_value=ctx),
        patch(
            "services.signal_service.fetch_top_symbols_vs_usdt",
            return_value={
                "as_of": "2026-02-09T00:00:00+00:00",
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "source": "mock",
                "degraded_reason": "",
            },
        ),
        patch(
            "services.signal_service.fetch_binance_klines",
            side_effect=lambda symbol, interval, limit: {
                "as_of": "2026-02-09T00:00:00+00:00",
                "symbol": symbol,
                "interval": interval,
                "candles": make_candles(120 if interval == "15m" else 260, start=100.0, step=0.8),
                "source": "mock",
                "degraded_reason": "",
            },
        ),
    ):
        svc = SignalService(
            settings=Settings(sqlite_path=str(tmp_path / "test_routes.db"), short_refresh_minutes=1, long_refresh_hours=1)
        )
        svc.refresh(force=True)
    return svc


def _get_test_client(tmp_path):
    """Build a TestClient with a mocked signal service singleton."""
    svc = _mock_signal_service_class(tmp_path)
    with patch("services.signal_service.get_signal_service", return_value=svc):
        # Also mock data sources used directly by report routes
        ctx = make_sample_context()
        with (
            patch("app.routes.report.fetch_all_sources", return_value=object()),
            patch("app.routes.report.compute_report_context", return_value=ctx),
        ):
            from app.main import create_app
            app = create_app()
            return TestClient(app), svc


def test_root_returns_html(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_signals_latest_returns_json(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/signals/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert "signals" in data
    assert "data_health" in data


def test_signals_symbol_valid(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/signals/BTCUSDT?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTCUSDT"
    assert "signals" in data


def test_signals_symbol_invalid_returns_422(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/signals/!!!")
    assert resp.status_code == 422


def test_regime_current_returns_json(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/regime/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "regime" in data
    assert "data_health" in data


def test_report_weekly_invalid_lang_returns_422(tmp_path):
    client, _ = _get_test_client(tmp_path)
    resp = client.get("/report/weekly?lang=fr")
    assert resp.status_code == 422
