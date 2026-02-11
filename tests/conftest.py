import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from report.schema import ReportContext


class FakeResponse:
    """Minimal fake urllib response for tests."""

    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def make_sample_context(macro_events_overrides: dict | None = None, **overrides) -> ReportContext:
    """Build a ReportContext with sensible test defaults.

    Args:
        macro_events_overrides: Partial overrides merged into the default macro_events dict.
        **overrides: Top-level ReportContext field overrides (replace entire field).
    """
    kwargs = {
        "as_of": "2026-02-09",
        "macro_events": {
            "cpi_release": "2026-02-13",
            "cpi_headline_yoy": 3.1,
            "cpi_headline_yoy_prev": 2.9,
            "cpi_headline_yoy_expected": None,
            "cpi_core_yoy": 3.3,
            "cpi_core_yoy_prev": 3.2,
            "cpi_core_yoy_expected": None,
            "nfp_release": "2026-02-07",
            "nfp_payroll_change": 165_000,
            "nfp_payroll_change_prev": 220_000,
            "nfp_payroll_change_expected": None,
            "nfp_unemployment_rate": 3.8,
            "nfp_unemployment_rate_prev": 4.0,
            "pmi_level": 52.4,
            "pmi_level_prev": 54.1,
            "pmi_level_expected": None,
            "pmi_state": "expansion",
            "fomc_next_meeting": "2026-03-18",
            "event_risk_week": True,
        },
        "rates": {"yield_curve_slope": -0.3, "ten_year": 4.05, "two_year": 4.35},
        "fedwatch": {"probabilities": {"cut": 0.25, "hold": 0.55, "hike": 0.20}},
        "cme_gap": {"status": "gap_up", "gap": 150},
        "derivatives": {
            "funding_rate": 0.01,
            "funding_state": "neutral",
            "open_interest": 21_500_000_000,
            "open_interest_change_7d": -0.03,
            "open_interest_state": "stable",
        },
        "stablecoin_flows": {"net_flow_24h": -250_000_000, "net_flow_7d": 1_200_000_000},
        "polymarket_markets": [
            {
                "question": "Will the Fed cut rates at the March 2026 FOMC meeting?",
                "outcomes": {"Yes": 0.25, "No": 0.75},
                "volume_usd": 120_000,
                "end_date": "2026-03-19",
                "slug": "test-fomc-cut",
            },
        ],
    }
    if macro_events_overrides:
        kwargs["macro_events"] = {**kwargs["macro_events"], **macro_events_overrides}
    kwargs.update(overrides)
    return ReportContext(**kwargs)


def make_candles(n: int, start: float = 100.0, step: float = 0.5) -> list[dict]:
    """Generate a list of synthetic OHLCV candles for testing."""
    out = []
    price = start
    for idx in range(n):
        price += step
        out.append(
            {
                "open_time": idx,
                "open": price - 0.2,
                "high": price + 0.8,
                "low": price - 0.9,
                "close": price,
                "volume": 1000 + idx * 8,
                "close_time": idx + 1,
            }
        )
    return out
