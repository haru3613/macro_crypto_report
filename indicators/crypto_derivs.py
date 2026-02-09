"""Crypto derivatives indicators."""


def derive_derivatives_state(derivs: dict) -> dict:
    funding = derivs["funding_rate"]
    open_interest_change = derivs["open_interest_change_7d"]
    if funding > 0.02:
        funding_state = "overheated"
    elif funding < 0:
        funding_state = "short_bias"
    else:
        funding_state = "neutral"

    if open_interest_change > 0.05:
        oi_state = "expanding"
    elif open_interest_change < -0.05:
        oi_state = "deleveraging"
    else:
        oi_state = "stable"

    return {
        "funding_rate": funding,
        "funding_state": funding_state,
        "open_interest": derivs["open_interest"],
        "open_interest_change_7d": open_interest_change,
        "open_interest_state": oi_state,
    }
