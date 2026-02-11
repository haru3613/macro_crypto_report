"""Schema for report context."""

from dataclasses import asdict, dataclass
from typing import Any, TypedDict


class RatesContext(TypedDict):
    yield_curve_slope: float
    ten_year: float
    two_year: float


class MacroEventsContext(TypedDict, total=False):
    cpi_release: str
    cpi_headline_yoy: float
    cpi_headline_yoy_prev: float
    cpi_headline_yoy_expected: float | None
    cpi_core_yoy: float
    cpi_core_yoy_prev: float
    cpi_core_yoy_expected: float | None
    nfp_release: str
    nfp_payroll_change: int
    nfp_payroll_change_prev: int
    nfp_payroll_change_expected: int | None
    nfp_unemployment_rate: float
    nfp_unemployment_rate_prev: float
    pmi_level: float
    pmi_level_prev: float
    pmi_level_expected: float | None
    pmi_state: str
    fomc_next_meeting: str
    event_risk_week: bool


@dataclass(frozen=True)
class ReportContext:
    as_of: str
    macro_events: MacroEventsContext
    rates: RatesContext
    fedwatch: dict[str, Any]
    cme_gap: dict[str, Any]
    derivatives: dict[str, Any]
    stablecoin_flows: dict[str, Any]
    polymarket_markets: list[dict[str, Any]] = None  # type: ignore[assignment]
    placeholder_sources: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.polymarket_markets is None:
            object.__setattr__(self, "polymarket_markets", [])
        if self.placeholder_sources is None:
            object.__setattr__(self, "placeholder_sources", [])

    def model_dump(self) -> dict[str, Any]:
        """Equivalent to dataclasses.asdict(self)."""
        return asdict(self)
