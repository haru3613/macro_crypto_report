# macro_crypto_report

Weekly macro + crypto report service with FastAPI.

## Features

- `GET /report/weekly` endpoint that returns:
- computed `context` JSON
- rendered `report_markdown`
- `GET /report/weekly/advice` endpoint that returns:
- `context` + `report_markdown` + `ai_advice` (analysis + suggestions)
- `signals_summary` for short-term and long-term actions
- `GET /signals/latest` returns latest actionable signals for all symbols
- `GET /signals/{symbol}` returns signal history for one symbol
- `GET /regime/current` returns macro/volatility regime + leverage multiplier
- Data pipeline for:
- CPI, NFP, PMI, FOMC schedule
- FedWatch probabilities
- Yield curve (10Y/2Y)
- CME gap, funding/OI state, stablecoin flow
- Binance OHLCV (15m, 1d) and CoinGecko top symbols (BTC/ETH + Top10 default)
- Indicator layer for curve slope, derivatives state, macro event summary, and CME gap
- Signal engine with EMA/RSI/ATR + conservative risk sizing
- SQLite storage for signals, regime, data health, and raw snapshots

## Data Source Status

- `data/sources/rates.py` now fetches live 10Y/2Y from FRED CSV (`DGS10`, `DGS2`) with fallback values.
- Market symbols and OHLCV are live from CoinGecko/Binance public APIs.
- Some macro/derivatives sources are still placeholder-backed and should be upgraded to full live APIs.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run API

```powershell
uvicorn app.main:app --reload
```

Then open:
- Dashboard: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Weekly report: `http://127.0.0.1:8000/report/weekly`
- Weekly report + AI advice: `http://127.0.0.1:8000/report/weekly/advice`
- Chinese weekly report: `http://127.0.0.1:8000/report/weekly?lang=zh-TW`
- English weekly report: `http://127.0.0.1:8000/report/weekly?lang=en`
- Chinese weekly advice: `http://127.0.0.1:8000/report/weekly/advice?lang=zh-TW`
- English weekly advice: `http://127.0.0.1:8000/report/weekly/advice?lang=en`
- Latest signals: `http://127.0.0.1:8000/signals/latest`
- Symbol history: `http://127.0.0.1:8000/signals/BTCUSDT`
- Current regime: `http://127.0.0.1:8000/regime/current`

Dashboard now includes a language switcher (Traditional Chinese / English) and defaults to Traditional Chinese.

## Optional AI Configuration

Set environment variables if you want model-generated advice:

```powershell
$env:GEMINI_API_KEY="your_api_key"
$env:GEMINI_MODEL="gemini-2.0-flash"
```

If `GEMINI_API_KEY` is missing or request fails, the service returns rule-based fallback advice.

## Optional Runtime Configuration

```powershell
$env:SQLITE_PATH="runtime/macro_crypto.db"
$env:TOP_N_SYMBOLS="10"
$env:SHORT_REFRESH_MINUTES="15"
$env:LONG_REFRESH_HOURS="24"
```

## Run Tests

```powershell
python -m pytest -q
```
