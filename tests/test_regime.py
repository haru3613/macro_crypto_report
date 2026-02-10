"""Tests for regime derivation edge cases."""

from signals.config import RegimeConfig
from signals.regime import derive_regime_state


def test_risk_off_bias_on_deep_inversion():
    regime = derive_regime_state(
        yield_curve_slope=-0.5,
        event_risk_week=False,
        btc_daily_volatility=0.03,
    )
    assert regime.macro_regime == "risk_off_bias"


def test_risk_on_bias_on_steep_curve():
    regime = derive_regime_state(
        yield_curve_slope=0.5,
        event_risk_week=False,
        btc_daily_volatility=0.03,
    )
    assert regime.macro_regime == "risk_on_bias"


def test_neutral_at_boundary():
    regime = derive_regime_state(
        yield_curve_slope=0.0,
        event_risk_week=False,
        btc_daily_volatility=0.03,
    )
    assert regime.macro_regime == "neutral"


def test_high_vol_regime():
    regime = derive_regime_state(
        yield_curve_slope=0.0,
        event_risk_week=False,
        btc_daily_volatility=0.06,
    )
    assert regime.vol_regime == "high_vol"


def test_low_vol_regime():
    regime = derive_regime_state(
        yield_curve_slope=0.0,
        event_risk_week=False,
        btc_daily_volatility=0.01,
    )
    assert regime.vol_regime == "low_vol"


def test_zero_volatility():
    regime = derive_regime_state(
        yield_curve_slope=0.0,
        event_risk_week=False,
        btc_daily_volatility=0.0,
    )
    assert regime.vol_regime == "low_vol"
    assert regime.leverage_multiplier == 1.0


def test_all_multipliers_active():
    """When event risk, high vol, and risk-off all stack."""
    regime = derive_regime_state(
        yield_curve_slope=-0.5,
        event_risk_week=True,
        btc_daily_volatility=0.06,
    )
    expected = round(1.0 * 0.65 * 0.7 * 0.8, 3)
    assert regime.leverage_multiplier == expected
    assert regime.macro_regime == "risk_off_bias"
    assert regime.vol_regime == "high_vol"


def test_leverage_clamped_to_min():
    """Even with extreme multiplier stacking, leverage stays >= 0.2."""
    config = RegimeConfig(
        event_risk_multiplier=0.1,
        high_vol_multiplier=0.1,
        risk_off_multiplier=0.1,
    )
    regime = derive_regime_state(
        yield_curve_slope=-0.5,
        event_risk_week=True,
        btc_daily_volatility=0.06,
        config=config,
    )
    assert regime.leverage_multiplier == 0.2


def test_custom_config_thresholds():
    config = RegimeConfig(yield_curve_risk_off=-0.1, yield_curve_risk_on=0.05)
    regime = derive_regime_state(
        yield_curve_slope=-0.15,
        event_risk_week=False,
        btc_daily_volatility=0.03,
        config=config,
    )
    assert regime.macro_regime == "risk_off_bias"
