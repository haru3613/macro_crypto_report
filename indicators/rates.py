"""Rates indicators."""


def compute_curve_slope(yield_curve: dict) -> float:
    """Compute 10Y-2Y slope in percentage points."""
    return yield_curve["ten_year"] - yield_curve["two_year"]
