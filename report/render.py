"""Render markdown report from context."""

from report.prompt import get_report_template
from report.schema import ReportContext


def _fmt_expected(value: float | int | None) -> str:
    """Format an optional expected/consensus value; None → 'N/A'."""
    return "N/A" if value is None else str(value)


def _fmt_polymarket_section(markets: list[dict]) -> str:
    """Format Polymarket markets as a markdown table."""
    if not markets:
        return "*No active macro prediction markets found.*"
    lines = ["| Question | Yes | No | Volume (USD) | Expires |",
             "|---|---|---|---|---|"]
    for m in markets:
        outcomes = m.get("outcomes", {})
        yes_p = outcomes.get("Yes")
        no_p = outcomes.get("No")
        yes_str = f"{yes_p:.0%}" if yes_p is not None else "—"
        no_str = f"{no_p:.0%}" if no_p is not None else "—"
        vol = f"${m.get('volume_usd', 0):,}"
        end = m.get("end_date", "")
        q = m.get("question", "")
        lines.append(f"| {q} | {yes_str} | {no_str} | {vol} | {end} |")
    return "\n".join(lines)


def render_report(context: ReportContext, lang: str = "en") -> str:
    me = context.macro_events
    template = get_report_template(lang)
    return template.format(
        as_of=context.as_of,
        curve_slope=context.rates["yield_curve_slope"],
        ten_year=context.rates["ten_year"],
        two_year=context.rates["two_year"],
        cpi_release=me["cpi_release"],
        cpi_headline_yoy=me["cpi_headline_yoy"],
        cpi_headline_yoy_prev=me["cpi_headline_yoy_prev"],
        cpi_headline_expected=_fmt_expected(me["cpi_headline_yoy_expected"]),
        cpi_core_yoy=me["cpi_core_yoy"],
        cpi_core_yoy_prev=me["cpi_core_yoy_prev"],
        cpi_core_expected=_fmt_expected(me["cpi_core_yoy_expected"]),
        nfp_release=me["nfp_release"],
        nfp_payroll_change=me["nfp_payroll_change"],
        nfp_payroll_change_prev=me["nfp_payroll_change_prev"],
        nfp_payroll_expected=_fmt_expected(me["nfp_payroll_change_expected"]),
        nfp_unemployment_rate=me["nfp_unemployment_rate"],
        nfp_unemployment_rate_prev=me["nfp_unemployment_rate_prev"],
        pmi_level=me["pmi_level"],
        pmi_level_prev=me["pmi_level_prev"],
        pmi_expected=_fmt_expected(me["pmi_level_expected"]),
        pmi_state=me["pmi_state"],
        fomc_meeting=me["fomc_next_meeting"],
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
        stablecoin_total_mcap=context.stablecoin_flows.get("total_mcap", 0),
        gap_status=context.cme_gap["status"],
        gap_value=context.cme_gap.get("gap", 0),
        polymarket_section=_fmt_polymarket_section(context.polymarket_markets),
    )
