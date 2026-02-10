"""Signal engine for short-term and long-term strategies."""

from statistics import mean

from signals.config import LongSignalConfig, ShortSignalConfig
from signals.schema import Signal
from signals.ta import atr, ema, pct_change, rsi


def _normalize_confidence(base: float) -> float:
    """Clamp confidence to [0.05, 0.95] and round to 3 decimals."""
    return round(max(0.05, min(0.95, base)), 3)


def _position_size_pct(confidence: float, leverage_multiplier: float, cfg_max: float = 0.08, cfg_base: float = 0.03, cfg_scale: float = 0.06) -> float:
    """Compute per-symbol position size as a fraction of portfolio.

    Formula: min(max, base + confidence * scale) * leverage_multiplier.
    """
    return round(min(cfg_max, cfg_base + confidence * cfg_scale) * leverage_multiplier, 4)


def _insufficient_data_signal(symbol: str, timeframe: str) -> Signal:
    """Return a degraded hold signal when there is not enough candle data."""
    return Signal(
        symbol=symbol,
        timeframe=timeframe,
        action="hold",
        confidence=0.15 if timeframe == "15m" else 0.2,
        risk_score=0.75 if timeframe == "15m" else 0.7,
        entry_low=0.0,
        entry_high=0.0,
        stop_loss=0.0,
        tp1=0.0,
        tp2=0.0,
        position_size_pct=0.0,
        invalidation=f"insufficient_{timeframe}_data",
        rationale_codes=["DATA_MISSING"],
        data_quality="degraded",
    )


def _zero_hold_fields(action: str, stop_loss: float, tp1: float, tp2: float, position_pct: float):
    """Zero out price/position fields when the action is hold."""
    if action == "hold":
        return 0.0, 0.0, 0.0, 0.0
    return stop_loss, tp1, tp2, position_pct


def build_short_signal(
    symbol: str,
    candles: list[dict],
    leverage_multiplier: float,
    config: ShortSignalConfig = ShortSignalConfig(),
) -> Signal:
    """Generate a 15-minute short-term signal using EMA crossover, RSI confirmation, and volume ratio."""
    if len(candles) < config.min_candles:
        return _insufficient_data_signal(symbol, "15m")

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    price = closes[-1]
    ema_fast = ema(closes[-20:], config.ema_fast_period)
    ema_slow = ema(closes[-30:], config.ema_slow_period)
    signal_rsi = rsi(closes[-20:], config.rsi_period)
    signal_atr = atr(highs[-20:], lows[-20:], closes[-20:], config.atr_period)
    volume_ratio = volumes[-1] / max(1.0, mean(volumes[-config.volume_lookback:]))

    trend_up = price > ema_fast > ema_slow
    trend_down = price < ema_fast < ema_slow

    action = "hold"
    rationale = []
    confidence = config.hold_confidence
    if trend_up and config.rsi_bull_low <= signal_rsi <= config.rsi_bull_high and volume_ratio >= config.volume_ratio_threshold:
        action = "buy"
        rationale.extend(["EMA_BULL", "RSI_SUPPORTIVE"])
        confidence = config.base_buy_confidence + min(config.max_buy_volume_bonus, (volume_ratio - 1.0) * config.volume_bonus_scale)
    elif trend_down and config.rsi_bear_low <= signal_rsi <= config.rsi_bear_high and volume_ratio >= config.volume_ratio_threshold:
        action = "sell"
        rationale.extend(["EMA_BEAR", "RSI_BEARISH"])
        confidence = config.base_sell_confidence + min(config.max_sell_volume_bonus, (volume_ratio - 1.0) * config.volume_bonus_scale)
    else:
        rationale.append("NO_CLEAR_EDGE")

    confidence = _normalize_confidence(confidence)
    risk_score = round(1 - confidence, 3)
    band = max(price * config.band_pct, signal_atr * config.band_atr_mult)
    entry_low = round(price - band, 6)
    entry_high = round(price + band, 6)
    stop_dist = max(price * config.stop_pct, signal_atr * config.stop_atr_mult)
    stop_loss = round(price - stop_dist if action != "sell" else price + stop_dist, 6)
    tp1_dist = max(price * config.tp1_pct, signal_atr * config.tp1_atr_mult)
    tp2_dist = max(price * config.tp2_pct, signal_atr * config.tp2_atr_mult)
    tp1 = round(price + tp1_dist if action != "sell" else price - tp1_dist, 6)
    tp2 = round(price + tp2_dist if action != "sell" else price - tp2_dist, 6)

    position_pct = _position_size_pct(confidence, leverage_multiplier, config.max_position_pct, config.base_position_pct, config.position_confidence_scale)
    stop_loss, tp1, tp2, position_pct = _zero_hold_fields(action, stop_loss, tp1, tp2, position_pct)

    invalidation = f"Break of {'EMA{}'.format(config.ema_slow_period) if action == 'buy' else 'EMA{}'.format(config.ema_fast_period)} with volume expansion"
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


def build_long_signal(
    symbol: str,
    candles: list[dict],
    leverage_multiplier: float,
    macro_regime: str,
    config: LongSignalConfig = LongSignalConfig(),
) -> Signal:
    """Generate a daily long-term signal using EMA trend alignment, 30-day momentum, and macro regime."""
    if len(candles) < config.min_candles:
        return _insufficient_data_signal(symbol, "1d")

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    price = closes[-1]
    ema50 = ema(closes[-80:], config.ema_medium_period)
    ema200 = ema(
        closes[-config.ema_long_period:] if len(closes) >= config.ema_long_period else closes,
        min(config.ema_long_period, len(closes)),
    )
    atr_daily = atr(highs[-40:], lows[-40:], closes[-40:], config.atr_period)
    trend_30d = pct_change(closes[-1], closes[-30])
    drawdown_30d = pct_change(min(closes[-30:]), max(closes[-30:]))

    action = "hold"
    confidence = config.hold_confidence
    rationale = []
    if price > ema50 > ema200 and trend_30d > config.trend_30d_bull_threshold and macro_regime != "risk_off_bias":
        action = "accumulate"
        confidence = config.base_accumulate_confidence
        rationale.extend(["TREND_UP", "REGIME_SUPPORTIVE"])
    elif price < ema50 and trend_30d < config.trend_30d_bear_threshold:
        action = "reduce"
        confidence = config.base_reduce_confidence
        rationale.extend(["TREND_DOWN", "MOMENTUM_WEAK"])
    else:
        rationale.append("RANGE_OR_TRANSITION")

    if drawdown_30d < config.drawdown_penalty_threshold:
        confidence -= config.drawdown_penalty_amount
        rationale.append("DEEP_DRAWDOWN")

    confidence = _normalize_confidence(confidence)
    risk_score = round(1 - confidence, 3)
    band = max(price * config.band_pct, atr_daily * config.band_atr_mult)
    entry_low = round(price - band, 6)
    entry_high = round(price + band, 6)
    stop_dist = max(price * config.stop_pct, atr_daily * config.stop_atr_mult)
    stop_loss = round(price - stop_dist if action != "reduce" else price + stop_dist, 6)
    tp1 = round(price * (config.tp1_bull_mult if action != "reduce" else config.tp1_bear_mult), 6)
    tp2 = round(price * (config.tp2_bull_mult if action != "reduce" else config.tp2_bear_mult), 6)

    position_pct = _position_size_pct(confidence, leverage_multiplier)
    stop_loss, tp1, tp2, position_pct = _zero_hold_fields(action, stop_loss, tp1, tp2, position_pct)

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
