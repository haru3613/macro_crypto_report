"""Signal service orchestration and caching."""

from datetime import datetime, timedelta, timezone
from statistics import pstdev

from app.config import Settings, get_settings
from data.fetch_all import fetch_all_sources
from data.sources.market import fetch_binance_klines, fetch_top_symbols_vs_usdt
from indicators.compute import compute_report_context
from signals.engine import build_long_signal, build_short_signal
from signals.regime import derive_regime_state
from signals.schema import DataHealth, utc_now_iso
from storage.sqlite_store import SQLiteStore


class SignalService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.store = SQLiteStore(self.settings.sqlite_path)
        self.last_short_refresh: datetime | None = None
        self.last_long_refresh: datetime | None = None

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def _needs_refresh(self, last: datetime | None, delta: timedelta) -> bool:
        if last is None:
            return True
        return self._utc_now() - last >= delta

    def _calc_daily_volatility(self, candles: list[dict]) -> float:
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

    def refresh(self, force: bool = False) -> None:
        short_interval = timedelta(minutes=self.settings.short_refresh_minutes)
        long_interval = timedelta(hours=self.settings.long_refresh_hours)
        do_short = force or self._needs_refresh(self.last_short_refresh, short_interval)
        do_long = force or self._needs_refresh(self.last_long_refresh, long_interval)
        if not do_short and not do_long:
            return

        health_rows: list[DataHealth] = []

        macro_raw = fetch_all_sources()
        context = compute_report_context(macro_raw)

        symbols_payload = fetch_top_symbols_vs_usdt(limit=self.settings.top_n_symbols)
        symbols = symbols_payload["symbols"]
        self.store.save_raw_snapshot("symbols", symbols_payload, utc_now_iso())
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

        regime = derive_regime_state(
            yield_curve_slope=context.rates["yield_curve_slope"],
            event_risk_week=context.macro_events["event_risk_week"],
            btc_daily_volatility=btc_vol,
        )
        self.store.save_regime(regime)

        signals = []
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
                    sig = _force_degraded(sig, long_klines["degraded_reason"])
                signals.append(sig)

        self.store.insert_signals(signals)
        self.store.save_data_health(health_rows)
        if do_short:
            self.last_short_refresh = self._utc_now()
        if do_long:
            self.last_long_refresh = self._utc_now()

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


def _force_degraded(signal, reason: str):
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


def get_signal_service() -> SignalService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = SignalService()
    return _service_singleton
