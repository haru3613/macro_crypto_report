"""Render markdown report from context."""

from report.prompt import get_report_template
from report.schema import ReportContext


def render_report(context: ReportContext, lang: str = "en") -> str:
    template = get_report_template(lang)
    return template.format(
        as_of=context.as_of,
        curve_slope=context.rates["yield_curve_slope"],
        ten_year=context.rates["ten_year"],
        two_year=context.rates["two_year"],
        cpi_release=context.macro_events["cpi_release"],
        nfp_release=context.macro_events["nfp_release"],
        pmi_level=context.macro_events["pmi_level"],
        pmi_state=context.macro_events["pmi_state"],
        fomc_meeting=context.macro_events["fomc_next_meeting"],
        prob_cut=context.fedwatch["probabilities"]["cut"],
        prob_hold=context.fedwatch["probabilities"]["hold"],
        prob_hike=context.fedwatch["probabilities"]["hike"],
        funding_rate=context.derivatives["funding_rate"],
        funding_state=context.derivatives["funding_state"],
        open_interest=context.derivatives["open_interest"],
        oi_change=context.derivatives["open_interest_change_7d"],
        oi_state=context.derivatives["open_interest_state"],
        stablecoin_24h=context.stablecoin_flows["net_flow_24h"],
        stablecoin_7d=context.stablecoin_flows["net_flow_7d"],
        gap_status=context.cme_gap["status"],
        gap_value=context.cme_gap.get("gap", 0),
    )
