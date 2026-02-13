"""Macro event summaries."""

from data.fetch_all import RawReportData


def _pick_expected(source_value, consensus_value):
    """Prefer Finnhub consensus; fall back to source-level value (usually None)."""
    if consensus_value is not None:
        return consensus_value
    return source_value


def _pick_release(source_value, consensus_value):
    """Prefer economic-calendar release date when available."""
    if consensus_value:
        return consensus_value
    return source_value


def summarize_macro_events(raw_data: RawReportData) -> dict:
    con = raw_data.consensus  # Finnhub economic consensus
    cpi = raw_data.cpi  # may be None
    nfp = raw_data.nfp  # may be None

    pmi_level = con.get("pmi_level_actual")
    if pmi_level is None:
        pmi_level = raw_data.pmi["headline"]

    result = {
        "pmi_level": pmi_level,
        "pmi_level_prev": con.get("pmi_level_prev") if con.get("pmi_level_prev") is not None else raw_data.pmi["headline_prev"],
        "pmi_level_expected": _pick_expected(
            raw_data.pmi["headline_expected"],
            con.get("pmi_level_expected"),
        ),
        "pmi_state": "expansion" if pmi_level >= 50 else "contraction",
        "fomc_next_meeting": raw_data.fomc["next_meeting"],
        "event_risk_week": True,
    }

    # CPI — may be None (unavailable)
    if cpi is not None:
        result.update({
            "cpi_release": _pick_release(cpi["release_date"], con.get("cpi_release_date")),
            "cpi_headline_yoy": cpi["headline_yoy"],
            "cpi_headline_yoy_prev": cpi["headline_yoy_prev"],
            "cpi_headline_yoy_expected": _pick_expected(
                cpi["headline_yoy_expected"],
                con.get("cpi_headline_yoy_expected"),
            ),
            "cpi_core_yoy": cpi["core_yoy"],
            "cpi_core_yoy_prev": cpi["core_yoy_prev"],
            "cpi_core_yoy_expected": _pick_expected(
                cpi["core_yoy_expected"],
                con.get("cpi_core_yoy_expected"),
            ),
        })
    else:
        result.update({
            "cpi_release": None,
            "cpi_headline_yoy": None,
            "cpi_headline_yoy_prev": None,
            "cpi_headline_yoy_expected": None,
            "cpi_core_yoy": None,
            "cpi_core_yoy_prev": None,
            "cpi_core_yoy_expected": None,
        })

    # NFP — may be None (unavailable)
    if nfp is not None:
        result.update({
            "nfp_release": _pick_release(nfp["release_date"], con.get("nfp_release_date")),
            "nfp_payroll_change": nfp["payroll_change"],
            "nfp_payroll_change_prev": nfp["payroll_change_prev"],
            "nfp_payroll_change_expected": _pick_expected(
                nfp["payroll_change_expected"],
                con.get("nfp_payroll_change_expected"),
            ),
            "nfp_unemployment_rate": nfp["unemployment_rate"],
            "nfp_unemployment_rate_prev": nfp["unemployment_rate_prev"],
        })
    else:
        result.update({
            "nfp_release": None,
            "nfp_payroll_change": None,
            "nfp_payroll_change_prev": None,
            "nfp_payroll_change_expected": None,
            "nfp_unemployment_rate": None,
            "nfp_unemployment_rate_prev": None,
        })

    return result
