"""Render markdown report from context."""

from report.prompt import get_report_template
from report.schema import ReportContext


def _na(value) -> str:
    """Format a value that may be None → 'N/A'."""
    return "N/A" if value is None else str(value)


def _pct(value, decimals: int = 1) -> str:
    """Format a float as percentage string; None → 'N/A'."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _comma(value) -> str:
    """Format a number with comma separators; None → 'N/A'."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def _signed_comma(value) -> str:
    """Format a number with sign and comma separators; None → 'N/A'."""
    if value is None:
        return "N/A"
    return f"{value:+,}"


def _pct_ratio(value) -> str:
    """Format a ratio (0-1) as percentage; None → 'N/A'."""
    if value is None:
        return "N/A"
    return f"{value:.0%}"


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
        curve_slope=_pct(context.rates["yield_curve_slope"], 2),
        ten_year=_pct(context.rates["ten_year"], 2),
        two_year=_pct(context.rates["two_year"], 2),
        cpi_release=_na(me.get("cpi_release")),
        cpi_headline_yoy=_pct(me.get("cpi_headline_yoy")),
        cpi_headline_yoy_prev=_pct(me.get("cpi_headline_yoy_prev")),
        cpi_headline_expected=_fmt_expected(me.get("cpi_headline_yoy_expected")),
        cpi_core_yoy=_pct(me.get("cpi_core_yoy")),
        cpi_core_yoy_prev=_pct(me.get("cpi_core_yoy_prev")),
        cpi_core_expected=_fmt_expected(me.get("cpi_core_yoy_expected")),
        nfp_release=_na(me.get("nfp_release")),
        nfp_payroll_change=_signed_comma(me.get("nfp_payroll_change")),
        nfp_payroll_change_prev=_signed_comma(me.get("nfp_payroll_change_prev")),
        nfp_payroll_expected=_fmt_expected(me.get("nfp_payroll_change_expected")),
        nfp_unemployment_rate=_pct(me.get("nfp_unemployment_rate")),
        nfp_unemployment_rate_prev=_pct(me.get("nfp_unemployment_rate_prev")),
        pmi_level=me["pmi_level"],
        pmi_level_prev=me["pmi_level_prev"],
        pmi_expected=_fmt_expected(me["pmi_level_expected"]),
        pmi_state=me["pmi_state"],
        fomc_meeting=me["fomc_next_meeting"],
        prob_cut=_pct_ratio(context.fedwatch["probabilities"]["cut"]),
        prob_hold=_pct_ratio(context.fedwatch["probabilities"]["hold"]),
        prob_hike=_pct_ratio(context.fedwatch["probabilities"]["hike"]),
        funding_rate=_pct(context.derivatives["funding_rate"], 3),
        funding_state=context.derivatives["funding_state"],
        open_interest=_comma(context.derivatives["open_interest"]),
        oi_change=_pct_ratio(context.derivatives["open_interest_change_7d"]),
        oi_state=context.derivatives["open_interest_state"],
        stablecoin_24h=_comma(context.stablecoin_flows["net_flow_24h"]),
        stablecoin_7d=_comma(context.stablecoin_flows["net_flow_7d"]),
        stablecoin_total_mcap=_comma(context.stablecoin_flows.get("total_mcap", 0)),
        gap_status=context.cme_gap["status"],
        gap_value=_comma(context.cme_gap.get("gap", 0)),
        polymarket_section=_fmt_polymarket_section(context.polymarket_markets),
    )
