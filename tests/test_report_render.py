from report.render import render_report
from report.schema import ReportContext


def test_report_render_contains_sections():
    context = ReportContext(
        as_of="2026-02-09",
        macro_events={
            "cpi_release": "2026-02-13",
            "cpi_headline_yoy": 3.1,
            "cpi_headline_yoy_prev": 2.9,
            "cpi_headline_yoy_expected": None,
            "cpi_core_yoy": 3.3,
            "cpi_core_yoy_prev": 3.2,
            "cpi_core_yoy_expected": None,
            "nfp_release": "2026-02-07",
            "nfp_payroll_change": 165_000,
            "nfp_payroll_change_prev": 220_000,
            "nfp_payroll_change_expected": None,
            "nfp_unemployment_rate": 3.8,
            "nfp_unemployment_rate_prev": 4.0,
            "pmi_level": 52.4,
            "pmi_level_prev": 54.1,
            "pmi_level_expected": None,
            "pmi_state": "expansion",
            "fomc_next_meeting": "2026-03-18",
        },
        rates={"yield_curve_slope": -0.3, "ten_year": 4.05, "two_year": 4.35},
        fedwatch={"probabilities": {"cut": 0.25, "hold": 0.55, "hike": 0.20}},
        cme_gap={"status": "gap_up", "gap": 150, "prev_close": 43000, "current_open": 43150},
        derivatives={
            "funding_rate": 0.01,
            "funding_state": "neutral",
            "open_interest": 21_500_000_000,
            "open_interest_change_7d": -0.03,
            "open_interest_state": "stable",
        },
        stablecoin_flows={"net_flow_24h": -250_000_000, "net_flow_7d": 1_200_000_000},
    )

    report = render_report(context)
    assert "Macro + Crypto Weekly Brief" in report
    assert "FedWatch" in report
