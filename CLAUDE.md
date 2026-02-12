# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run API server (with hot reload)
uvicorn app.main:app --reload

# Run all tests
python -m pytest -q

# Run single test file
python -m pytest tests/test_signal_engine.py -v

# Run specific test
python -m pytest tests/test_regime.py::test_risk_off_bias_on_deep_inversion -v

# Docker
docker compose up --build
```

## Architecture

**Data pipeline**: `data/sources/` → `data/fetch_all.py` → `indicators/compute.py` → `report/` + `signals/`

The system fetches from 9 external sources (FRED, Binance, CoinGecko, DefiLlama, etc.), each with a try/except fallback to placeholder data. Every source dict includes an `is_placeholder: bool` field. The `indicators/compute.py` layer transforms `RawReportData` into a `ReportContext`, collecting which sources used fallback data into `placeholder_sources`.

**Signal engine** (`signals/engine.py`): Generates two timeframes:
- **15m short-term**: EMA 9/21 crossover + RSI 14 + volume ratio → buy/sell/hold
- **1d long-term**: EMA 50/200 trend + 30d momentum + macro regime filter → accumulate/reduce/hold

Both use ATR-based entry/stop/TP bands and confidence-based position sizing (3-8% of portfolio × leverage multiplier).

**Regime derivation** (`signals/regime.py`): Yield curve slope + BTC daily volatility + event risk → macro regime (risk_off_bias/neutral/risk_on_bias) + vol regime → leverage multiplier [0.2, 1.0].

**Service layer** (`services/signal_service.py`): Thread-safe singleton with dual refresh cycles (15m short, 24h long). Uses double-checked locking. On source failure, produces degraded hold signals with confidence ≤ 0.2.

**Storage**: SQLite via `storage/sqlite_store.py`. Tables: signals, regimes, data_health, raw_snapshots.

## Key Conventions

- **Python 3.13, dataclasses (not Pydantic)**, frozen=True for immutability. `model_dump()` wraps `dataclasses.asdict()`.
- **No heavy dependencies** — stdlib `urllib`/`json`/`csv`/`sqlite3` for I/O, no pandas/numpy.
- **Multilingual**: Templates in `report/prompt.py` (en + zh-TW). Frontend i18n in `app/static/app.js`. User communicates in Traditional Chinese.
- **Config**: `app/config.py` loads from `.env` via python-dotenv. All env vars documented in `.env.example`.
- **Signal configs** (`signals/config.py`): `ShortSignalConfig`, `LongSignalConfig`, `RegimeConfig` — frozen dataclasses with all thresholds as fields, no magic numbers in engine code.
- **Test fixtures** in `tests/conftest.py`: `FakeResponse`, `make_sample_context()`, `make_candles()`. Tests mock all external API calls.

## API Endpoints

- `GET /` — Dashboard (static HTML)
- `GET /report/weekly?lang={en|zh-TW}` — Context + markdown report
- `GET /report/weekly/advice?lang={en|zh-TW}` — Above + AI advice + signal summary
- `GET /report/weekly/ai?lang={en|zh-TW}` — AI advice only
- `GET /report/weekly/fed-chair?lang={en|zh-TW}` — Fed Chair (Powell-style) FOMC dual-mandate policy analysis
- `GET /signals/latest` — Latest signals for all symbols
- `GET /signals/{symbol}?limit=40` — Signal history (symbol validated: `^[A-Z0-9]{2,20}$`)
- `GET /regime/current` — Current macro/vol regime + leverage multiplier

## Data Source Status

| Source | API | Key Required |
|--------|-----|-------------|
| Yield curve | FRED CSV (DGS10/DGS2) | No |
| CPI, NFP | FRED JSON API (with prev values) | FRED_API_KEY |
| ISM PMI | **Placeholder only** (NAPM discontinued) | — |
| Symbols | CoinGecko markets | No |
| Klines | Binance spot | No |
| Funding/OI | Binance Futures | No |
| CME gap | Binance daily (proxy) | No |
| Stablecoin flows | DefiLlama | No |
| FOMC schedule | Static 2025-2026 calendar | No |
| FedWatch | **Placeholder only** (no free API) | — |
| Consensus estimates | FMP (paid) → Investing.com (free fallback) | FMP_API_KEY (optional) |
| Polymarket | Gamma API (macro markets) | No |
| AI advice | Rules engine (Claude subagent for full analysis) | No |
| Fed Chair agent | Rules engine (Claude subagent for full analysis) | No |

## AI Analysis (Claude Subagent)

AI-powered analysis is done via Claude Code subagent instead of external APIs.

**Prompts**: `prompts/weekly_ai_advice.md` and `prompts/fed_chair_analysis.md`

**Workflow**:
1. Run `python scripts/export_context.py` to get current data (or fetch from running API)
2. Ask Claude to analyze using the prompt + data
3. API endpoints (`/weekly/ai`, `/weekly/fed-chair`) provide rules-based fallback
