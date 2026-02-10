from signals.summary import summarize_signals


def test_signals_summary_contract_shape():
    signals = [
        {"timeframe": "15m", "action": "buy"},
        {"timeframe": "15m", "action": "sell"},
        {"timeframe": "15m", "action": "hold"},
        {"timeframe": "1d", "action": "accumulate"},
        {"timeframe": "1d", "action": "reduce"},
        {"timeframe": "1d", "action": "hold"},
    ]
    out = summarize_signals(signals)
    assert set(out.keys()) == {"15m", "1d"}
    assert set(out["15m"].keys()) == {"buy", "sell", "hold"}
    assert set(out["1d"].keys()) == {"accumulate", "reduce", "hold"}
