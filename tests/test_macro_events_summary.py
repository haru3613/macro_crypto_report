from data.fetch_all import RawReportData
from indicators.macro_events import summarize_macro_events


def test_macro_events_prefers_consensus_release_and_pmi_actual():
    raw = RawReportData(
        cpi={
            "release_date": "2025-12-01",
            "headline_yoy": 2.7,
            "headline_yoy_prev": 2.6,
            "headline_yoy_expected": None,
            "core_yoy": 2.9,
            "core_yoy_prev": 2.8,
            "core_yoy_expected": None,
            "is_placeholder": False,
        },
        nfp={
            "release_date": "2026-01-01",
            "payroll_change": 130000,
            "payroll_change_prev": 48000,
            "payroll_change_expected": None,
            "unemployment_rate": 4.3,
            "unemployment_rate_prev": 4.4,
            "is_placeholder": False,
        },
        pmi={
            "headline": 52.4,
            "headline_prev": 54.1,
            "headline_expected": None,
            "is_placeholder": True,
        },
        fomc={"next_meeting": "2026-03-18", "is_placeholder": False},
        fedwatch={"is_placeholder": True},
        yield_curve={"ten_year": 4.1, "two_year": 3.4, "is_placeholder": False},
        crypto_derivs={"is_placeholder": False},
        stablecoin_flows={"is_placeholder": False},
        cme_ohlc=[{"is_placeholder": False}],
        polymarket={"is_placeholder": False},
        consensus={
            "cpi_release_date": "2026-01-13",
            "nfp_release_date": "2026-02-11",
            "pmi_level_actual": 50.8,
            "pmi_level_prev": 49.9,
            "pmi_level_expected": 51.1,
            "is_placeholder": False,
        },
    )

    me = summarize_macro_events(raw)
    assert me["cpi_release"] == "2026-01-13"
    assert me["nfp_release"] == "2026-02-11"
    assert me["pmi_level"] == 50.8
    assert me["pmi_level_prev"] == 49.9
