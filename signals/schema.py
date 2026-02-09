"""Schemas for actionable signal service."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Signal:
    symbol: str
    timeframe: str
    action: str
    confidence: float
    risk_score: float
    entry_low: float
    entry_high: float
    stop_loss: float
    tp1: float
    tp2: float
    position_size_pct: float
    invalidation: str
    rationale_codes: list[str]
    data_quality: str
    as_of: str = field(default_factory=utc_now_iso)

    def model_dump(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RegimeState:
    macro_regime: str
    event_risk_week: bool
    vol_regime: str
    leverage_multiplier: float
    as_of: str = field(default_factory=utc_now_iso)

    def model_dump(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DataHealth:
    source_name: str
    last_ok_at: str
    staleness_sec: int
    degraded_reason: str

    def model_dump(self) -> dict:
        return asdict(self)
