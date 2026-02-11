"""SQLite storage for signals/regime/data health."""

import json
import sqlite3
from pathlib import Path

from signals.schema import DataHealth, RegimeState, Signal


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    entry_low REAL NOT NULL,
                    entry_high REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    tp1 REAL NOT NULL,
                    tp2 REAL NOT NULL,
                    position_size_pct REAL NOT NULL,
                    invalidation TEXT NOT NULL,
                    rationale_codes TEXT NOT NULL,
                    data_quality TEXT NOT NULL,
                    as_of TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_signals_symbol_tf_asof
                    ON signals(symbol, timeframe, as_of DESC);

                CREATE TABLE IF NOT EXISTS regimes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    macro_regime TEXT NOT NULL,
                    event_risk_week INTEGER NOT NULL,
                    vol_regime TEXT NOT NULL,
                    leverage_multiplier REAL NOT NULL,
                    as_of TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS data_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    last_ok_at TEXT NOT NULL,
                    staleness_sec INTEGER NOT NULL,
                    degraded_reason TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS raw_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    as_of TEXT NOT NULL
                );
                """
            )

    def insert_signals(self, signals: list[Signal]) -> None:
        if not signals:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO signals (
                    symbol, timeframe, action, confidence, risk_score, entry_low, entry_high,
                    stop_loss, tp1, tp2, position_size_pct, invalidation, rationale_codes,
                    data_quality, as_of
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        s.symbol,
                        s.timeframe,
                        s.action,
                        s.confidence,
                        s.risk_score,
                        s.entry_low,
                        s.entry_high,
                        s.stop_loss,
                        s.tp1,
                        s.tp2,
                        s.position_size_pct,
                        s.invalidation,
                        json.dumps(s.rationale_codes),
                        s.data_quality,
                        s.as_of,
                    )
                    for s in signals
                ],
            )

    def latest_signals(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*
                FROM signals s
                INNER JOIN (
                    SELECT symbol, timeframe, MAX(as_of) AS latest_asof
                    FROM signals
                    GROUP BY symbol, timeframe
                ) x ON s.symbol = x.symbol
                   AND s.timeframe = x.timeframe
                   AND s.as_of = x.latest_asof
                ORDER BY s.symbol, s.timeframe
                """
            ).fetchall()
        return [self._signal_row_to_dict(row) for row in rows]

    def signals_for_symbol(self, symbol: str, limit: int = 40) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM signals
                WHERE symbol = ?
                ORDER BY as_of DESC
                LIMIT ?
                """,
                (symbol.upper(), limit),
            ).fetchall()
        return [self._signal_row_to_dict(row) for row in rows]

    def save_regime(self, regime: RegimeState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO regimes (macro_regime, event_risk_week, vol_regime, leverage_multiplier, as_of)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    regime.macro_regime,
                    int(regime.event_risk_week),
                    regime.vol_regime,
                    regime.leverage_multiplier,
                    regime.as_of,
                ),
            )

    def latest_regime(self) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM regimes ORDER BY as_of DESC LIMIT 1").fetchone()
        if row is None:
            return None
        return {
            "macro_regime": row["macro_regime"],
            "event_risk_week": bool(row["event_risk_week"]),
            "vol_regime": row["vol_regime"],
            "leverage_multiplier": row["leverage_multiplier"],
            "as_of": row["as_of"],
        }

    def save_data_health(self, health_rows: list[DataHealth]) -> None:
        if not health_rows:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM data_health")
            conn.executemany(
                """
                INSERT INTO data_health (source_name, last_ok_at, staleness_sec, degraded_reason)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (h.source_name, h.last_ok_at, h.staleness_sec, h.degraded_reason)
                    for h in health_rows
                ],
            )

    def latest_data_health(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM data_health ORDER BY source_name").fetchall()
        return [
            {
                "source_name": row["source_name"],
                "last_ok_at": row["last_ok_at"],
                "staleness_sec": row["staleness_sec"],
                "degraded_reason": row["degraded_reason"],
            }
            for row in rows
        ]

    def save_raw_snapshot(self, source_name: str, payload: dict, as_of: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO raw_snapshots (source_name, payload, as_of) VALUES (?, ?, ?)",
                (source_name, json.dumps(payload), as_of),
            )

    @staticmethod
    def _signal_row_to_dict(row: sqlite3.Row) -> dict:
        return {
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "action": row["action"],
            "confidence": row["confidence"],
            "risk_score": row["risk_score"],
            "entry_low": row["entry_low"],
            "entry_high": row["entry_high"],
            "stop_loss": row["stop_loss"],
            "tp1": row["tp1"],
            "tp2": row["tp2"],
            "position_size_pct": row["position_size_pct"],
            "invalidation": row["invalidation"],
            "rationale_codes": json.loads(row["rationale_codes"]),
            "data_quality": row["data_quality"],
            "as_of": row["as_of"],
        }
