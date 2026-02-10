"""Signal service orchestration and caching."""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import pstdev
from typing import Any

logger = logging.getLogger(__name__)

from app.config import Settings, get_settings
from data.fetch_all import fetch_all_sources
from data.sources.market import fetch_binance_klines, fetch_top_symbols_vs_usdt
from indicators.compute import compute_report_context
from report.schema import ReportContext
from signals.engine import build_long_signal, build_short_signal
from signals.regime import derive_regime_state
from signals.schema import DataHealth, RegimeState, Signal, utc_now_iso
from storage.sqlite_store import SQLiteStore


@dataclass
class MarketSnapshot:
    """Aggregated market data fetched during a refresh cycle."""

    context: ReportContext
    symbols: list[str]
    btc_volatility: float
    health_rows: list[DataHealth] = field(default_factory=list)
    raw_snapshots: list[tuple[str, dict[str, Any], str]] = field(default_factory=list)


class SignalService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.store = SQLiteStore(self.settings.sqlite_path)
        self.last_short_refresh: datetime | None = None
        self.last_long_refresh: datetime | None = None
        self._refresh_lock = threading.Lock()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def _needs_refresh(self, last: datetime | None, delta: timedelta) -> bool:
        if last is None:
            return True
        return self._utc_now() - last >= delta

    @staticmethod
    def _calc_daily_volatility(candles: list[dict]) -> float:
        closes = [c["close"] for c in candles]
        if len(closes) < 8:
            return 0.0
        returns = []
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            if prev == 0:
                continue
            returns.append((closes[idx] - prev) / prev)
        if len(returns) < 5:
            return 0.0
        return float(pstdev(returns))

    def _fetch_market_data(self) -> MarketSnapshot:
        """Fetch all external data needed for signal generation."""
        health_rows: list[DataHealth] = []

        macro_raw = fetch_all_sources()
        context = compute_report_context(macro_raw)

        symbols_payload = fetch_top_symbols_vs_usdt(limit=self.settings.top_n_symbols)
        symbols = symbols_payload["symbols"]
        health_rows.append(
            DataHealth(
                source_name="coingecko_symbols",
                last_ok_at=symbols_payload["as_of"],
                staleness_sec=0,
                degraded_reason=symbols_payload["degraded_reason"],
            )
        )

        btc_daily = fetch_binance_klines("BTCUSDT", "1d", 90)
        btc_vol = self._calc_daily_volatility(btc_daily["candles"])
        health_rows.append(
            DataHealth(
                source_name="binance_btc_1d",
                last_ok_at=btc_daily["as_of"],
                staleness_sec=0,
                degraded_reason=btc_daily["degraded_reason"],
            )
        )

        return MarketSnapshot(
            context=context,
            symbols=symbols,
            btc_volatility=btc_vol,
            health_rows=health_rows,
            raw_snapshots=[("symbols", symbols_payload, utc_now_iso())],
        )

    def _build_signals_for_symbols(
        self,
        symbols: list[str],
        regime: RegimeState,
        do_short: bool,
        do_long: bool,
    ) -> tuple[list[Signal], list[DataHealth]]:
        """Build short and/or long signals for each symbol."""
        signals: list[Signal] = []
        health_rows: list[DataHealth] = []

        for symbol in symbols:
            if do_short:
                short_klines = fetch_binance_klines(symbol, "15m", 120)
                health_rows.append(
                    DataHealth(
                        source_name=f"binance_{symbol}_15m",
                        last_ok_at=short_klines["as_of"],
                        staleness_sec=0,
                        degraded_reason=short_klines["degraded_reason"],
                    )
                )
                sig = build_short_signal(symbol, short_klines["candles"], regime.leverage_multiplier)
                if short_klines["degraded_reason"]:
                    logger.warning("Degraded short signal for %s: %s", symbol, short_klines["degraded_reason"])
                    sig = _force_degraded(sig, short_klines["degraded_reason"])
                signals.append(sig)

            if do_long:
                long_klines = fetch_binance_klines(symbol, "1d", 260)
                health_rows.append(
                    DataHealth(
                        source_name=f"binance_{symbol}_1d",
                        last_ok_at=long_klines["as_of"],
                        staleness_sec=0,
                        degraded_reason=long_klines["degraded_reason"],
                    )
                )
                sig = build_long_signal(
                    symbol=symbol,
                    candles=long_klines["candles"],
                    leverage_multiplier=regime.leverage_multiplier,
                    macro_regime=regime.macro_regime,
                )
                if long_klines["degraded_reason"]:
                    logger.warning("Degraded long signal for %s: %s", symbol, long_klines["degraded_reason"])
                    sig = _force_degraded(sig, long_klines["degraded_reason"])
                signals.append(sig)

        return signals, health_rows

    def refresh(self, force: bool = False) -> None:
        short_interval = timedelta(minutes=self.settings.short_refresh_minutes)
        long_interval = timedelta(hours=self.settings.long_refresh_hours)
        do_short = force or self._needs_refresh(self.last_short_refresh, short_interval)
        do_long = force or self._needs_refresh(self.last_long_refresh, long_interval)
        if not do_short and not do_long:
            return

        with self._refresh_lock:
            # Re-check after acquiring lock to avoid redundant work.
            do_short = force or self._needs_refresh(self.last_short_refresh, short_interval)
            do_long = force or self._needs_refresh(self.last_long_refresh, long_interval)
            if not do_short and not do_long:
                return

            logger.info("Signal refresh started (short=%s, long=%s)", do_short, do_long)

            snapshot = self._fetch_market_data()
            for name, payload, ts in snapshot.raw_snapshots:
                self.store.save_raw_snapshot(name, payload, ts)

            regime = derive_regime_state(
                yield_curve_slope=snapshot.context.rates["yield_curve_slope"],
                event_risk_week=snapshot.context.macro_events["event_risk_week"],
                btc_daily_volatility=snapshot.btc_volatility,
            )
            self.store.save_regime(regime)

            signals, signal_health = self._build_signals_for_symbols(
                snapshot.symbols, regime, do_short, do_long,
            )

            all_health = snapshot.health_rows + signal_health
            self.store.insert_signals(signals)
            self.store.save_data_health(all_health)

            if do_short:
                self.last_short_refresh = self._utc_now()
            if do_long:
                self.last_long_refresh = self._utc_now()
            logger.info("Signal refresh completed, %d signals stored", len(signals))

    def latest_signals(self) -> list[dict]:
        self.refresh()
        return self.store.latest_signals()

    def signals_for_symbol(self, symbol: str, limit: int = 40) -> list[dict]:
        self.refresh()
        return self.store.signals_for_symbol(symbol=symbol, limit=limit)

    def current_regime(self) -> dict:
        self.refresh()
        regime = self.store.latest_regime()
        if regime is None:
            return {
                "macro_regime": "unknown",
                "event_risk_week": False,
                "vol_regime": "unknown",
                "leverage_multiplier": 0.5,
                "as_of": utc_now_iso(),
            }
        return regime

    def data_health(self) -> list[dict]:
        self.refresh()
        return self.store.latest_data_health()


def _force_degraded(signal: Signal, reason: str) -> Signal:
    return type(signal)(
        **{
            **signal.model_dump(),
            "action": "hold",
            "confidence": min(signal.confidence, 0.2),
            "risk_score": max(signal.risk_score, 0.75),
            "position_size_pct": 0.0,
            "data_quality": "degraded",
            "rationale_codes": ["DATA_DEGRADED", reason],
            "invalidation": reason,
        }
    )


_service_singleton: SignalService | None = None
_service_lock = threading.Lock()


def get_signal_service() -> SignalService:
    global _service_singleton
    if _service_singleton is not None:
        return _service_singleton
    with _service_lock:
        if _service_singleton is None:
            _service_singleton = SignalService()
    return _service_singleton
