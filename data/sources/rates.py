"""Rates data source."""

import csv
import io
from datetime import date
from urllib.request import urlopen

FRED_DGS10_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
FRED_DGS2_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2"


def _fetch_latest_fred_rate(csv_url: str, column: str) -> tuple[str, float]:
    with urlopen(csv_url, timeout=10) as response:
        text = response.read().decode("utf-8")

    rows = list(csv.DictReader(io.StringIO(text)))
    for row in reversed(rows):
        value = row.get(column, "")
        if value and value != ".":
            return row["DATE"], float(value)
    raise ValueError(f"No valid values found for {column}")


def fetch_yield_curve() -> dict:
    try:
        ten_year_date, ten_year = _fetch_latest_fred_rate(FRED_DGS10_CSV, "DGS10")
        two_year_date, two_year = _fetch_latest_fred_rate(FRED_DGS2_CSV, "DGS2")
        as_of = min(ten_year_date, two_year_date)
        return {
            "as_of": as_of,
            "ten_year": ten_year,
            "two_year": two_year,
            "source": "FRED DGS10/DGS2",
        }
    except Exception:
        return {
            "as_of": date(2026, 2, 9).isoformat(),
            "ten_year": 4.05,
            "two_year": 4.35,
            "source": "Treasury yields (placeholder fallback)",
        }
