"""Technical indicators used by signal engine."""


def ema(values: list[float], period: int) -> float:
    """Exponential Moving Average.

    Uses the standard smoothing factor alpha = 2 / (period + 1).
    Iterates through the series applying: EMA_t = alpha * value_t + (1 - alpha) * EMA_{t-1}.
    """
    if not values:
        return 0.0
    alpha = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1 - alpha) * result
    return result


def rsi(values: list[float], period: int = 14) -> float:
    """Relative Strength Index (0-100).

    Computes average gain / average loss over the lookback period.
    Returns 50.0 (neutral) when insufficient data, 100.0 when no losses.
    """
    if len(values) < period + 1:
        return 50.0
    gains = []
    losses = []
    for idx in range(1, len(values)):
        change = values[idx] - values[idx - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float:
    """Average True Range.

    True Range = max(high - low, |high - prev_close|, |low - prev_close|).
    Returns the simple average of the last `period` true range values.
    """
    if len(highs) < 2 or len(lows) < 2 or len(closes) < 2:
        return 0.0
    trs: list[float] = []
    for idx in range(1, len(closes)):
        high = highs[idx]
        low = lows[idx]
        prev_close = closes[idx - 1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if not trs:
        return 0.0
    window = trs[-period:] if len(trs) >= period else trs
    return sum(window) / len(window)


def pct_change(a: float, b: float) -> float:
    """Percentage change from b to a: (a - b) / b."""
    if b == 0:
        return 0.0
    return (a - b) / b
