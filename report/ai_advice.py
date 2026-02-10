"""Generate AI analysis and suggestions from report context."""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

from app.config import Settings, get_settings
from report.schema import ReportContext

SYSTEM_PROMPT_EN = """You are a macro+crypto risk analyst.
Given a structured report context and markdown brief, return a concise analysis with:
1) Market regime
2) Top risks this week
3) Actionable trade/risk-management suggestions
4) Invalid setup / what to avoid
Keep recommendations specific, practical, and risk-aware.
Use markdown with short bullet points.
"""

SYSTEM_PROMPT_ZH = """你是宏觀與加密市場風險分析師。
請根據結構化 report context 與週報內容，輸出精簡分析，包含：
1) 當前市場型態
2) 本週核心風險
3) 可執行的交易/風控建議
4) 無效情境與應避免行為
請使用繁體中文與 markdown 短條列。
"""


def _system_prompt(lang: str) -> str:
    if lang.lower().startswith("zh"):
        return SYSTEM_PROMPT_ZH
    return SYSTEM_PROMPT_EN


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    lines: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                lines.append(content["text"])
    return "\n".join(lines).strip()


def _fallback_advice(context: ReportContext, lang: str = "en") -> str:
    curve_slope = context.rates["yield_curve_slope"]
    funding_state = context.derivatives["funding_state"]
    oi_state = context.derivatives["open_interest_state"]
    stablecoin_24h = context.stablecoin_flows["net_flow_24h"]
    event_risk = context.macro_events.get("event_risk_week", False)

    regime = "mixed"
    if curve_slope < 0 and stablecoin_24h < 0:
        regime = "risk-off bias"
    elif funding_state == "overheated" and oi_state == "expanding":
        regime = "late risk-on with crowding"
    elif stablecoin_24h > 0 and oi_state in {"stable", "expanding"}:
        regime = "cautious risk-on"

    risk_items = []
    if event_risk:
        risk_items.append("Macro event risk is elevated around CPI/NFP/FOMC timing.")
    if funding_state == "overheated":
        risk_items.append("Funding is overheated; long squeeze probability is higher.")
    if oi_state == "deleveraging":
        risk_items.append("Open interest is deleveraging; trend continuation can weaken.")
    if curve_slope < 0:
        risk_items.append("Yield curve remains inverted; medium-term macro fragility persists.")
    if stablecoin_24h < 0:
        risk_items.append("Stablecoin net outflow suggests weaker immediate crypto demand.")
    if not risk_items:
        risk_items.append("No single extreme signal, but cross-asset confirmation is limited.")

    actions = [
        "Keep position sizing smaller during event windows; avoid adding leverage pre-release.",
        "Prefer confirmation entries after data prints instead of predicting binary outcomes.",
        "Use invalidation levels and hard stops; avoid averaging down into high-volatility moves.",
    ]
    if funding_state == "overheated":
        actions.append("Consider reducing long exposure or using partial hedge when basis is crowded.")
    if stablecoin_24h < 0:
        actions.append("Require stronger spot/volume confirmation before risk-on entries.")

    avoid = [
        "Do not run oversized leverage ahead of CPI/NFP outcomes.",
        "Do not treat one metric (only funding or only OI) as a full directional signal.",
    ]

    if lang.lower().startswith("zh"):
        regime_map = {
            "risk-off bias": "偏風險趨避",
            "late risk-on with crowding": "偏風險偏好但擁擠",
            "cautious risk-on": "謹慎風險偏好",
            "mixed": "混合盤",
        }
        risk_items_zh = [
            "CPI/NFP/FOMC 時窗的宏觀事件風險偏高。" if event_risk else None,
            "Funding 過熱，發生 long squeeze 的機率提高。" if funding_state == "overheated" else None,
            "OI 去槓桿中，趨勢延續力可能下降。" if oi_state == "deleveraging" else None,
            "殖利率曲線仍倒掛，中期宏觀脆弱性仍在。" if curve_slope < 0 else None,
            "穩定幣淨流出，短線需求偏弱。" if stablecoin_24h < 0 else None,
        ]
        risk_rows = [item for item in risk_items_zh if item]
        if not risk_rows:
            risk_rows = ["未見單一極端訊號，但跨資產確認仍有限。"]
        action_rows = [
            "事件公布前縮小部位與槓桿，不預判二元結果。",
            "優先等待資料公布後的確認訊號再進場。",
            "採用明確失效價與硬停損，避免高波動下攤平。",
        ]
        if funding_state == "overheated":
            action_rows.append("基差擁擠時考慮降長倉或用部分對沖。")
        if stablecoin_24h < 0:
            action_rows.append("風險偏好進場前，先要求更強的現貨/量能確認。")
        avoid_rows = [
            "避免在 CPI/NFP 前使用過大槓桿。",
            "避免只看單一指標（例如只看 Funding 或只看 OI）就做方向判斷。",
        ]
        return (
            f"## AI 分析（Fallback）\n"
            f"- 市場型態：**{regime_map.get(regime, regime)}**\n\n"
            f"## 核心風險\n"
            + "\n".join(f"- {item}" for item in risk_rows)
            + "\n\n## 建議\n"
            + "\n".join(f"- {item}" for item in action_rows)
            + "\n\n## 應避免\n"
            + "\n".join(f"- {item}" for item in avoid_rows)
        )

    return (
        f"## AI Analysis (Fallback)\n"
        f"- Regime: **{regime}**\n\n"
        f"## Top Risks\n"
        + "\n".join(f"- {item}" for item in risk_items)
        + "\n\n## Suggestions\n"
        + "\n".join(f"- {item}" for item in actions)
        + "\n\n## Avoid\n"
        + "\n".join(f"- {item}" for item in avoid)
    )


def generate_ai_advice(
    context: ReportContext,
    report_markdown: str,
    lang: str = "en",
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    if not settings.openai_api_key:
        return {
            "analysis_markdown": _fallback_advice(context, lang=lang),
            "source": "fallback_rules",
            "model": "none",
        }

    request_body = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "max_output_tokens": 800,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": _system_prompt(lang)}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Language preference: {lang}\n\n"
                            "Structured context JSON:\n"
                            f"{json.dumps(context.model_dump(), ensure_ascii=True)}\n\n"
                            "Markdown brief:\n"
                            f"{report_markdown}"
                        ),
                    }
                ],
            },
        ],
    }

    try:
        req = Request(
            settings.openai_base_url,
            data=json.dumps(request_body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = _extract_output_text(payload)
        if not text:
            raise ValueError("Empty model response")
        return {
            "analysis_markdown": text,
            "source": "openai",
            "model": settings.openai_model,
        }
    except Exception as exc:
        logger.error("OpenAI API call failed, falling back to rules: %s", exc)
        return {
            "analysis_markdown": _fallback_advice(context, lang=lang),
            "source": "fallback_rules",
            "model": settings.openai_model,
            "error": str(exc),
        }
