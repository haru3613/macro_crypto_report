from conftest import make_candles
from signals.engine import build_long_signal, build_short_signal


def test_build_short_signal_has_actionable_fields():
    signal = build_short_signal("BTCUSDT", make_candles(120), leverage_multiplier=0.8)
    assert signal.symbol == "BTCUSDT"
    assert signal.timeframe == "15m"
    assert signal.action in {"buy", "sell", "hold"}
    assert signal.data_quality in {"ok", "degraded"}
    assert signal.position_size_pct >= 0


def test_build_long_signal_has_actionable_fields():
    signal = build_long_signal(
        "ETHUSDT",
        make_candles(260, start=2000, step=3.0),
        leverage_multiplier=0.7,
        macro_regime="neutral",
    )
    assert signal.symbol == "ETHUSDT"
    assert signal.timeframe == "1d"
    assert signal.action in {"accumulate", "reduce", "hold"}
    assert signal.data_quality in {"ok", "degraded"}


def test_insufficient_data_degrades_signal():
    signal = build_short_signal("BTCUSDT", make_candles(5), leverage_multiplier=1.0)
    assert signal.data_quality == "degraded"
    assert signal.action == "hold"
