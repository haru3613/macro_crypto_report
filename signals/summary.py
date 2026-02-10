"""Signal summary utilities."""


def summarize_signals(signals: list[dict]) -> dict:
    summary: dict[str, dict[str, int]] = {
        "15m": {"buy": 0, "sell": 0, "hold": 0},
        "1d": {"accumulate": 0, "reduce": 0, "hold": 0},
    }
    for signal in signals:
        timeframe = signal["timeframe"]
        action = signal["action"]
        if timeframe in summary and action in summary[timeframe]:
            summary[timeframe][action] += 1
    return summary
