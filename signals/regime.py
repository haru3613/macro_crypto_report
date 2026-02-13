"""Regime state derivation."""

from signals.config import RegimeConfig
from signals.schema import RegimeState


def derive_regime_state(
    yield_curve_slope: float | None,
    event_risk_week: bool,
    btc_daily_volatility: float,
    config: RegimeConfig = RegimeConfig(),
) -> RegimeState:
    macro_regime = "neutral"
    if yield_curve_slope is not None:
        if yield_curve_slope < config.yield_curve_risk_off:
            macro_regime = "risk_off_bias"
        elif yield_curve_slope > config.yield_curve_risk_on:
            macro_regime = "risk_on_bias"

    if btc_daily_volatility >= config.vol_high_threshold:
        vol_regime = "high_vol"
    elif btc_daily_volatility <= config.vol_low_threshold:
        vol_regime = "low_vol"
    else:
        vol_regime = "normal_vol"

    leverage_multiplier = 1.0
    if event_risk_week:
        leverage_multiplier *= config.event_risk_multiplier
    if vol_regime == "high_vol":
        leverage_multiplier *= config.high_vol_multiplier
    if macro_regime == "risk_off_bias":
        leverage_multiplier *= config.risk_off_multiplier
    leverage_multiplier = max(config.leverage_min, min(config.leverage_max, leverage_multiplier))

    return RegimeState(
        macro_regime=macro_regime,
        event_risk_week=event_risk_week,
        vol_regime=vol_regime,
        leverage_multiplier=round(leverage_multiplier, 3),
    )
