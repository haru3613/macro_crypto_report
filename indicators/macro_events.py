"""Macro event summaries."""

from data.fetch_all import RawReportData


def summarize_macro_events(raw_data: RawReportData) -> dict:
    return {
        "cpi_release": raw_data.cpi["release_date"],
        "nfp_release": raw_data.nfp["release_date"],
        "pmi_level": raw_data.pmi["headline"],
        "pmi_state": "expansion" if raw_data.pmi["headline"] >= 50 else "contraction",
        "fomc_next_meeting": raw_data.fomc["next_meeting"],
        "event_risk_week": True,
    }
