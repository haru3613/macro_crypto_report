from report.render import render_report
from report.schema import ReportContext


def test_report_render_contains_sections():
    context = ReportContext(
        as_of="2026-02-09",
        macro_events={
            "cpi_release": "2026-02-13",
            "nfp_release": "2026-02-07",
            "pmi_level": 52.4,
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
