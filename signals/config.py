"""Configurable thresholds and parameters for signal generation and regime derivation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ShortSignalConfig:
    """Parameters for 15-minute short-term signal generation."""

    min_candles: int = 40
    ema_fast_period: int = 9
    ema_slow_period: int = 21
    rsi_period: int = 14
    atr_period: int = 14
    volume_lookback: int = 20
    # RSI thresholds
    rsi_bull_low: float = 46.0
    rsi_bull_high: float = 68.0
    rsi_bear_low: float = 32.0
    rsi_bear_high: float = 55.0
    volume_ratio_threshold: float = 0.9
    # Confidence
    base_buy_confidence: float = 0.62
    base_sell_confidence: float = 0.60
    max_buy_volume_bonus: float = 0.2
    max_sell_volume_bonus: float = 0.18
    volume_bonus_scale: float = 0.1
    hold_confidence: float = 0.35
    # Entry band
    band_pct: float = 0.0025
    band_atr_mult: float = 0.25
    # Stop loss
    stop_pct: float = 0.005
    stop_atr_mult: float = 0.8
    # Take profit
    tp1_pct: float = 0.007
    tp1_atr_mult: float = 1.2
    tp2_pct: float = 0.012
    tp2_atr_mult: float = 2.0
    # Position sizing
    max_position_pct: float = 0.08
    base_position_pct: float = 0.03
    position_confidence_scale: float = 0.06


@dataclass(frozen=True)
class LongSignalConfig:
    """Parameters for daily long-term signal generation."""

    min_candles: int = 80
    ema_medium_period: int = 50
    ema_long_period: int = 200
    atr_period: int = 14
    # Trend thresholds
    trend_30d_bull_threshold: float = 0.02
    trend_30d_bear_threshold: float = -0.04
    # Drawdown penalty
    drawdown_penalty_threshold: float = -0.15
    drawdown_penalty_amount: float = 0.08
    # Confidence
    base_accumulate_confidence: float = 0.68
    base_reduce_confidence: float = 0.66
    hold_confidence: float = 0.4
    # Entry band
    band_pct: float = 0.008
    band_atr_mult: float = 0.5
    # Stop loss
    stop_pct: float = 0.03
    stop_atr_mult: float = 1.8
    # Take profit multipliers (applied to price)
    tp1_bull_mult: float = 1.08
    tp1_bear_mult: float = 0.93
    tp2_bull_mult: float = 1.15
    tp2_bear_mult: float = 0.88


@dataclass(frozen=True)
class RegimeConfig:
    """Parameters for macro/volatility regime derivation."""

    # Yield curve slope thresholds
    yield_curve_risk_off: float = -0.2
    yield_curve_risk_on: float = 0.1
    # BTC daily volatility thresholds
    vol_high_threshold: float = 0.045
    vol_low_threshold: float = 0.02
    # Leverage multiplier adjustments
    event_risk_multiplier: float = 0.65
    high_vol_multiplier: float = 0.7
    risk_off_multiplier: float = 0.8
    leverage_min: float = 0.2
    leverage_max: float = 1.0
