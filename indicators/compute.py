"""Compute report context from raw data sources."""

from datetime import date

from data.fetch_all import RawReportData
from indicators.crypto_derivs import derive_derivatives_state
from indicators.cme_gap import detect_cme_gap
from indicators.macro_events import summarize_macro_events
from indicators.rates import compute_curve_slope
from report.schema import ReportContext

# Mapping of source name → RawReportData field name for placeholder detection
_SOURCE_LABELS = {
    "cpi": "CPI",
    "nfp": "NFP",
    "pmi": "ISM PMI",
    "fomc": "FOMC",
    "fedwatch": "FedWatch",
    "yield_curve": "Yield Curve",
    "crypto_derivs": "Crypto Derivatives",
    "stablecoin_flows": "Stablecoin Flows",
    "polymarket": "Polymarket",
    "consensus": "Consensus Estimates",
}


def _collect_placeholder_sources(raw_data: RawReportData) -> list[str]:
    """Return list of human-readable names for sources using placeholder data."""
    placeholders = []
    for field_name, label in _SOURCE_LABELS.items():
        source_data = getattr(raw_data, field_name)
        if isinstance(source_data, dict) and source_data.get("is_placeholder", False):
            placeholders.append(label)

    # CME OHLC is a list of dicts; check first item
    cme_ohlc = raw_data.cme_ohlc
    if cme_ohlc and isinstance(cme_ohlc[0], dict) and cme_ohlc[0].get("is_placeholder", False):
        placeholders.append("CME OHLC")
    elif not cme_ohlc:
        placeholders.append("CME OHLC")

    return placeholders


def compute_report_context(raw_data: RawReportData) -> ReportContext:
    curve_slope = compute_curve_slope(raw_data.yield_curve)
    derivatives_state = derive_derivatives_state(raw_data.crypto_derivs)
    cme_gap = detect_cme_gap(raw_data.cme_ohlc)
    macro_events = summarize_macro_events(raw_data)
    placeholder_sources = _collect_placeholder_sources(raw_data)

    return ReportContext(
        as_of=date.today().isoformat(),
        macro_events=macro_events,
        rates={
            "yield_curve_slope": curve_slope,
            "ten_year": raw_data.yield_curve["ten_year"],
            "two_year": raw_data.yield_curve["two_year"],
        },
        fedwatch=raw_data.fedwatch,
        cme_gap=cme_gap,
        derivatives=derivatives_state,
        stablecoin_flows=raw_data.stablecoin_flows,
        polymarket_markets=raw_data.polymarket.get("markets", []),
        placeholder_sources=placeholder_sources,
    )
