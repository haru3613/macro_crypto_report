"""Compute report context from raw data sources."""

from datetime import date

from data.fetch_all import RawReportData
from indicators.crypto_derivs import derive_derivatives_state
from indicators.cme_gap import detect_cme_gap
from indicators.macro_events import summarize_macro_events
from indicators.rates import compute_curve_slope
from report.schema import ReportContext

# Mapping of source name → RawReportData field name for unavailability detection
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


def _collect_unavailable_sources(raw_data: RawReportData) -> list[str]:
    """Return list of human-readable names for sources that are unavailable or placeholder."""
    unavailable = []
    for field_name, label in _SOURCE_LABELS.items():
        source_data = getattr(raw_data, field_name)
        if source_data is None:
            unavailable.append(label)
        elif isinstance(source_data, dict) and source_data.get("is_placeholder", False):
            unavailable.append(f"{label} (placeholder)")

    # CME OHLC
    cme_ohlc = raw_data.cme_ohlc
    if cme_ohlc is None or not cme_ohlc:
        unavailable.append("CME OHLC")

    return unavailable


def compute_report_context(raw_data: RawReportData) -> ReportContext:
    # Rates — may be None
    if raw_data.yield_curve is not None:
        curve_slope = compute_curve_slope(raw_data.yield_curve)
        rates = {
            "yield_curve_slope": curve_slope,
            "ten_year": raw_data.yield_curve["ten_year"],
            "two_year": raw_data.yield_curve["two_year"],
        }
    else:
        rates = {"yield_curve_slope": None, "ten_year": None, "two_year": None}

    # Derivatives — may be None
    if raw_data.crypto_derivs is not None:
        derivatives_state = derive_derivatives_state(raw_data.crypto_derivs)
    else:
        derivatives_state = {
            "funding_rate": None,
            "funding_state": "unavailable",
            "open_interest": None,
            "open_interest_change_7d": None,
            "open_interest_state": "unavailable",
        }

    # CME gap — may be None
    if raw_data.cme_ohlc is not None:
        cme_gap = detect_cme_gap(raw_data.cme_ohlc)
    else:
        cme_gap = {"gap": None, "status": "unavailable"}

    macro_events = summarize_macro_events(raw_data)
    unavailable_sources = _collect_unavailable_sources(raw_data)

    # Stablecoin flows — may be None
    stablecoin_flows = raw_data.stablecoin_flows or {
        "as_of": date.today().isoformat(),
        "net_flow_24h": None,
        "net_flow_7d": None,
        "total_mcap": None,
        "source": "unavailable",
        "is_placeholder": False,
    }

    # Polymarket — may be None
    polymarket_markets = []
    if raw_data.polymarket is not None:
        polymarket_markets = raw_data.polymarket.get("markets", [])

    return ReportContext(
        as_of=date.today().isoformat(),
        macro_events=macro_events,
        rates=rates,
        fedwatch=raw_data.fedwatch,
        cme_gap=cme_gap,
        derivatives=derivatives_state,
        stablecoin_flows=stablecoin_flows,
        polymarket_markets=polymarket_markets,
        placeholder_sources=unavailable_sources,
    )
