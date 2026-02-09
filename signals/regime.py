"""Regime state derivation."""

from signals.schema import RegimeState


def derive_regime_state(
    yield_curve_slope: float,
    event_risk_week: bool,
    btc_daily_volatility: float,
) -> RegimeState:
    macro_regime = "neutral"
    if yield_curve_slope < -0.2:
        macro_regime = "risk_off_bias"
    elif yield_curve_slope > 0.1:
        macro_regime = "risk_on_bias"

    if btc_daily_volatility >= 0.045:
        vol_regime = "high_vol"
    elif btc_daily_volatility <= 0.02:
        vol_regime = "low_vol"
    else:
        vol_regime = "normal_vol"

    leverage_multiplier = 1.0
    if event_risk_week:
        leverage_multiplier *= 0.65
    if vol_regime == "high_vol":
        leverage_multiplier *= 0.7
    if macro_regime == "risk_off_bias":
        leverage_multiplier *= 0.8
    leverage_multiplier = max(0.2, min(1.0, leverage_multiplier))

    return RegimeState(
        macro_regime=macro_regime,
        event_risk_week=event_risk_week,
        vol_regime=vol_regime,
        leverage_multiplier=round(leverage_multiplier, 3),
    )
