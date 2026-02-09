"""Signal engine for short-term and long-term strategies."""

from statistics import mean

from signals.schema import Signal
from signals.ta import atr, ema, pct_change, rsi


def _normalize_confidence(base: float) -> float:
    return round(max(0.05, min(0.95, base)), 3)


def _position_size_pct(confidence: float, leverage_multiplier: float) -> float:
    # Conservative first version: cap per symbol at 8%.
    return round(min(0.08, 0.03 + confidence * 0.06) * leverage_multiplier, 4)


def build_short_signal(symbol: str, candles: list[dict], leverage_multiplier: float) -> Signal:
    if len(candles) < 40:
        return Signal(
            symbol=symbol,
            timeframe="15m",
            action="hold",
            confidence=0.15,
            risk_score=0.75,
            entry_low=0.0,
            entry_high=0.0,
            stop_loss=0.0,
            tp1=0.0,
            tp2=0.0,
            position_size_pct=0.0,
            invalidation="insufficient_15m_data",
            rationale_codes=["DATA_MISSING"],
            data_quality="degraded",
        )

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    price = closes[-1]
    ema_fast = ema(closes[-20:], 9)
    ema_slow = ema(closes[-30:], 21)
    signal_rsi = rsi(closes[-20:], 14)
    signal_atr = atr(highs[-20:], lows[-20:], closes[-20:], 14)
    volume_ratio = volumes[-1] / max(1.0, mean(volumes[-20:]))

    trend_up = price > ema_fast > ema_slow
    trend_down = price < ema_fast < ema_slow

    action = "hold"
    rationale = []
    confidence = 0.35
    if trend_up and 46 <= signal_rsi <= 68 and volume_ratio >= 0.9:
        action = "buy"
        rationale.extend(["EMA_BULL", "RSI_SUPPORTIVE"])
        confidence = 0.62 + min(0.2, (volume_ratio - 1.0) * 0.1)
    elif trend_down and 32 <= signal_rsi <= 55 and volume_ratio >= 0.9:
        action = "sell"
        rationale.extend(["EMA_BEAR", "RSI_BEARISH"])
        confidence = 0.60 + min(0.18, (volume_ratio - 1.0) * 0.1)
    else:
        rationale.append("NO_CLEAR_EDGE")

    confidence = _normalize_confidence(confidence)
    risk_score = round(1 - confidence, 3)
    band = max(price * 0.0025, signal_atr * 0.25)
    entry_low = round(price - band, 6)
    entry_high = round(price + band, 6)
    stop_dist = max(price * 0.005, signal_atr * 0.8)
    stop_loss = round(price - stop_dist if action != "sell" else price + stop_dist, 6)
    tp1_dist = max(price * 0.007, signal_atr * 1.2)
    tp2_dist = max(price * 0.012, signal_atr * 2.0)
    tp1 = round(price + tp1_dist if action != "sell" else price - tp1_dist, 6)
    tp2 = round(price + tp2_dist if action != "sell" else price - tp2_dist, 6)

    position_pct = _position_size_pct(confidence, leverage_multiplier)
    if action == "hold":
        position_pct = 0.0
        stop_loss = 0.0
        tp1 = 0.0
        tp2 = 0.0

    invalidation = f"Break of {'EMA21' if action == 'buy' else 'EMA9'} with volume expansion"
    return Signal(
        symbol=symbol,
        timeframe="15m",
        action=action,
        confidence=confidence,
        risk_score=risk_score,
        entry_low=entry_low,
        entry_high=entry_high,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        position_size_pct=position_pct,
        invalidation=invalidation,
        rationale_codes=rationale,
        data_quality="ok",
    )


def build_long_signal(symbol: str, candles: list[dict], leverage_multiplier: float, macro_regime: str) -> Signal:
    if len(candles) < 80:
        return Signal(
            symbol=symbol,
            timeframe="1d",
            action="hold",
            confidence=0.2,
            risk_score=0.7,
            entry_low=0.0,
            entry_high=0.0,
            stop_loss=0.0,
            tp1=0.0,
            tp2=0.0,
            position_size_pct=0.0,
            invalidation="insufficient_1d_data",
            rationale_codes=["DATA_MISSING"],
            data_quality="degraded",
        )

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    price = closes[-1]
    ema50 = ema(closes[-80:], 50)
    ema200 = ema(closes[-200:] if len(closes) >= 200 else closes, min(200, len(closes)))
    atr_daily = atr(highs[-40:], lows[-40:], closes[-40:], 14)
    trend_30d = pct_change(closes[-1], closes[-30])
    drawdown_30d = pct_change(min(closes[-30:]), max(closes[-30:]))

    action = "hold"
    confidence = 0.4
    rationale = []
    if price > ema50 > ema200 and trend_30d > 0.02 and macro_regime != "risk_off_bias":
        action = "accumulate"
        confidence = 0.68
        rationale.extend(["TREND_UP", "REGIME_SUPPORTIVE"])
    elif price < ema50 and trend_30d < -0.04:
        action = "reduce"
        confidence = 0.66
        rationale.extend(["TREND_DOWN", "MOMENTUM_WEAK"])
    else:
        rationale.append("RANGE_OR_TRANSITION")

    if drawdown_30d < -0.15:
        confidence -= 0.08
        rationale.append("DEEP_DRAWDOWN")

    confidence = _normalize_confidence(confidence)
    risk_score = round(1 - confidence, 3)
    band = max(price * 0.008, atr_daily * 0.5)
    entry_low = round(price - band, 6)
    entry_high = round(price + band, 6)
    stop_dist = max(price * 0.03, atr_daily * 1.8)
    stop_loss = round(price - stop_dist if action != "reduce" else price + stop_dist, 6)
    tp1 = round(price * (1.08 if action != "reduce" else 0.93), 6)
    tp2 = round(price * (1.15 if action != "reduce" else 0.88), 6)

    position_pct = _position_size_pct(confidence, leverage_multiplier)
    if action == "hold":
        position_pct = 0.0
        stop_loss = 0.0
        tp1 = 0.0
        tp2 = 0.0

    return Signal(
        symbol=symbol,
        timeframe="1d",
        action=action,
        confidence=confidence,
        risk_score=risk_score,
        entry_low=entry_low,
        entry_high=entry_high,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        position_size_pct=position_pct,
        invalidation="Daily close against trend and momentum breakdown",
        rationale_codes=rationale,
        data_quality="ok",
    )
