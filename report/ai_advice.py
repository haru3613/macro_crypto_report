"""Generate AI analysis and suggestions from report context.

AI analysis is now handled by Claude subagent (see prompts/weekly_ai_advice.md).
This module provides the rules-based fallback used by the API endpoints.
"""

import logging
from typing import Any

from report.schema import ReportContext

logger = logging.getLogger(__name__)


def _fallback_advice(context: ReportContext, lang: str = "en") -> str:
    """Deterministic rule-based advice when AI is unavailable."""
    curve_slope = context.rates["yield_curve_slope"]
    funding_state = context.derivatives["funding_state"]
    oi_state = context.derivatives["open_interest_state"]
    stablecoin_24h = context.stablecoin_flows["net_flow_24h"]
    event_risk = context.macro_events.get("event_risk_week", False)

    # Simple regime logic
    regime = "Mixed / Chop"
    if curve_slope < -0.5 and stablecoin_24h < -10000000:
        regime = "Risk-Off Bias"
    elif funding_state == "overheated" and oi_state == "expanding":
        regime = "Late Risk-On (Crowded)"
    elif stablecoin_24h > 0 and oi_state in {"stable", "expanding"}:
        regime = "Cautious Risk-On"

    is_zh = lang.lower().startswith("zh")

    text_map = {
        "regime_label": "市場型態" if is_zh else "Market Regime",
        "risks_label": "核心風險" if is_zh else "Top Risks",
        "suggestions_label": "建議" if is_zh else "Suggestions",
        "avoid_label": "應避免" if is_zh else "Avoid",
        "title": "AI 分析 (規則引擎)" if is_zh else "AI Analysis (Rules Engine)",
    }

    risks = []
    if event_risk:
        risks.append("宏觀事件風險偏高 (CPI/FOMC/NFP)" if is_zh else "Elevated macro event risk (CPI/FOMC/NFP).")
    if funding_state == "overheated":
        risks.append("費率過熱，多頭擠壓風險高" if is_zh else "Funding overheated; high long-squeeze probability.")
    if oi_state == "deleveraging":
        risks.append("OI 正在去槓桿，趨勢可能轉弱" if is_zh else "OI deleveraging; trend continuation weakening.")
    if not risks:
        risks.append("市場缺乏明確方向性訊號" if is_zh else "No single extreme signal; low conviction environment.")

    actions = [
        "縮小部位，等待事件落地" if is_zh else "Reduce sizing ahead of events.",
        "嚴格設定失效價，避免抗單" if is_zh else "Use hard stops; do not average down.",
    ]

    avoid = [
        "避免在資料發布前重倉押注" if is_zh else "Do not pre-position heavily before data prints."
    ]

    return (
        f"## {text_map['title']}\n"
        f"- {text_map['regime_label']}: **{regime}**\n\n"
        f"## {text_map['risks_label']}\n"
        + "\n".join(f"- {r}" for r in risks)
        + f"\n\n## {text_map['suggestions_label']}\n"
        + "\n".join(f"- {a}" for a in actions)
        + f"\n\n## {text_map['avoid_label']}\n"
        + "\n".join(f"- {a}" for a in avoid)
    )


def generate_ai_advice(
    context: ReportContext,
    report_markdown: str,
    lang: str = "en",
    settings: Any = None,
) -> dict[str, Any]:
    """Generate rules-based market analysis.

    Full AI analysis is done via Claude subagent (prompts/weekly_ai_advice.md).
    This function provides the deterministic fallback for the API endpoint.
    """
    return {
        "analysis_markdown": _fallback_advice(context, lang=lang),
        "source": "rules_engine",
        "model": "none",
    }
