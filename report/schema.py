"""Schema for report context."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReportContext:
    as_of: str
    macro_events: dict
    rates: dict
    fedwatch: dict
    cme_gap: dict
    derivatives: dict
    stablecoin_flows: dict

    def model_dump(self) -> dict:
        return asdict(self)
