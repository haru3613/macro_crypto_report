"""Schema for report context."""

from dataclasses import asdict, dataclass
from typing import Any, TypedDict


class RatesContext(TypedDict):
    yield_curve_slope: float
    ten_year: float
    two_year: float


class MacroEventsContext(TypedDict, total=False):
    cpi_release: str
    nfp_release: str
    pmi_level: float
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
    placeholder_sources: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.placeholder_sources is None:
            object.__setattr__(self, "placeholder_sources", [])

    def model_dump(self) -> dict[str, Any]:
        """Equivalent to dataclasses.asdict(self)."""
        return asdict(self)
