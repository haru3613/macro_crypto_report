from indicators.cme_gap import detect_cme_gap
from indicators.crypto_derivs import derive_derivatives_state
from indicators.rates import compute_curve_slope


def test_curve_slope():
    assert compute_curve_slope({"ten_year": 4.0, "two_year": 4.5}) == -0.5


def test_cme_gap():
    ohlc = [
        {"close": 100},
        {"open": 105},
    ]
    gap = detect_cme_gap(ohlc)
    assert gap["gap"] == 5
    assert gap["status"] == "gap_up"


def test_derivatives_state():
    derivs = {
        "funding_rate": 0.03,
        "open_interest": 1000,
        "open_interest_change_7d": -0.1,
    }
    state = derive_derivatives_state(derivs)
    assert state["funding_state"] == "overheated"
    assert state["open_interest_state"] == "deleveraging"
