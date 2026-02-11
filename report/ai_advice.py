"""Generate AI analysis and suggestions from report context."""

import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Dict, Any, Optional

from app.config import Settings, get_settings
from report.schema import ReportContext

logger = logging.getLogger(__name__)

# --- Prompts ---

SYSTEM_PROMPT_EN = """
Role: Macro & Crypto Risk Analyst.
Task: Analyze the provided Report Context (JSON) and Market Brief (Markdown) to generate a strategic summary.

Output Requirements:
1. **Market Regime**: Define the current state (e.g., Risk-On, Risk-Off, PVP, Chop).
2. **Top Risks**: Identify specific immediate risks (funding heat, macro events, liquidity).
3. **Actionable Suggestions**: Concrete execution or risk management steps.
4. **Invalidation/Avoid**: specific setups to ignore or conditions that invalidate the thesis.

Format: Markdown, concise bullet points. No conversational filler.
"""

SYSTEM_PROMPT_ZH = """
角色：宏觀與加密貨幣市場風險分析師。
任務：根據提供的結構化數據 (Report Context) 與市場簡報 (Markdown Brief) 生成策略摘要。

輸出要求：
1. **當前市場型態**：定義目前狀態（如：風險偏好上升、風險趨避、存量博弈、震盪洗盤）。
2. **本週核心風險**：具體的即時風險（如：費率過熱、宏觀事件、流動性缺失）。
3. **可執行的建議**：具體的交易或風控操作步驟。
4. **無效情境/應避免**：需要避開的無效交易結構或會推翻邏輯的條件。

格式：繁體中文 (Traditional Chinese)，Markdown 短條列，風格專業精簡。
"""

# Using v1beta to access latest features
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

def _system_prompt(lang: str) -> str:
    return SYSTEM_PROMPT_ZH if lang.lower().startswith("zh") else SYSTEM_PROMPT_EN

def _extract_gemini_text(payload: dict) -> tuple[str, str]:
    """Extract text and return (text, diagnostics)."""

    prompt_feedback = payload.get("promptFeedback", {})
    if prompt_feedback.get("blockReason"):
        reason = f"prompt_blocked:{prompt_feedback.get('blockReason')}"
        logger.error("Gemini Prompt Blocked. Reason: %s", prompt_feedback.get("blockReason"))
        return "", reason

    candidates = payload.get("candidates", [])
    if not candidates:
        logger.error("Gemini: No candidates returned. Raw payload: %s", json.dumps(payload))
        return "", "no_candidates"

    for idx, candidate in enumerate(candidates):
        finish_reason = candidate.get("finishReason")

        if finish_reason == "SAFETY":
            safety_ratings = candidate.get("safetyRatings", [])
            triggered = [
                f"{r.get('category', 'unknown')}={r.get('probability', 'unknown')}"
                for r in safety_ratings
                if r.get("probability") not in ["NEGLIGIBLE", "LOW"]
            ]
            logger.error("Gemini Safety Block. Triggers: %s", ", ".join(triggered))
            continue

        if finish_reason not in ["STOP", "MAX_TOKENS", None]:
            logger.warning("Gemini stopped unusually. Reason: %s", finish_reason)

        content = candidate.get("content", {})
        parts = content.get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        text = "\n".join(texts).strip()
        if text:
            return text, f"candidate_{idx}:{finish_reason or 'none'}"

    return "", "empty_text_in_all_candidates"

def _fallback_advice(context: ReportContext, lang: str = "en") -> str:
    """Deterministic rule-based advice when AI is unavailable."""
    curve_slope = context.rates["yield_curve_slope"]
    funding_state = context.derivatives["funding_state"]
    oi_state = context.derivatives["open_interest_state"]
    stablecoin_24h = context.stablecoin_flows["net_flow_24h"]
    event_risk = context.macro_events.get("event_risk_week", False)

    # Simple regime logic
    regime = "Mixed / Chop"
    if curve_slope < -0.5 and stablecoin_24h < -10000000: # Example thresholds
        regime = "Risk-Off Bias"
    elif funding_state == "overheated" and oi_state == "expanding":
        regime = "Late Risk-On (Crowded)"
    elif stablecoin_24h > 0 and oi_state in {"stable", "expanding"}:
        regime = "Cautious Risk-On"

    is_zh = lang.lower().startswith("zh")

    # Mapping for translation
    text_map = {
        "regime_label": "市場型態" if is_zh else "Market Regime",
        "risks_label": "核心風險" if is_zh else "Top Risks",
        "suggestions_label": "建議" if is_zh else "Suggestions",
        "avoid_label": "應避免" if is_zh else "Avoid",
        "fallback_title": "AI 分析 (Fallback)" if is_zh else "AI Analysis (Fallback)",
    }

    # Dynamic List Generation
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

    # Construct Markdown
    return (
        f"## {text_map['fallback_title']}\n"
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
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the API call to Gemini.
    """
    settings = settings or get_settings()
    
    # 1. Validation
    if not settings.gemini_api_key:
        return {
            "analysis_markdown": _fallback_advice(context, lang=lang),
            "source": "fallback_rules",
            "model": "none",
        }

    # 2. Prepare Context & Payload
    model_name = (settings.gemini_model or "gemini-2.0-flash").strip()
    
    # Construct URL
    url = GEMINI_API_URL.format(model=model_name) + "?" + urlencode({"key": settings.gemini_api_key})

    # Prepare input text
    # ensure_ascii=False is crucial for saving tokens and handling Chinese characters correctly
    context_str = json.dumps(context.model_dump(), ensure_ascii=False, indent=2)
    
    user_prompt = (
        f"Language: {lang}\n\n"
        f"### Quantitative Context (JSON)\n{context_str}\n\n"
        f"### Market Brief (Markdown)\n{report_markdown}"
    )

    # Disable safety filters for financial context (often triggers 'Financial Advice' or 'Gambling' filters falsely)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    request_body = {
        "system_instruction": {
            "parts": [{"text": _system_prompt(lang)}],
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Language preference: {lang}\n"
                            f"Context JSON: {json.dumps(context.model_dump(), ensure_ascii=False)}\n"
                            f"Report: {report_markdown}"
                        )
                    }
                ],
            }
        ],
        # INSERT SAFETY SETTINGS HERE
        "safetySettings": safety_settings,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
        },
    }

    # 3. Execute Request
    start_time = time.perf_counter()
    try:
        req = Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            
        text, diagnostics = _extract_gemini_text(payload)

        if not text:
            logger.warning("Gemini returned empty text but 200 OK. diagnostics=%s", diagnostics)
            raise ValueError(f"Empty model response ({diagnostics})")

        return {
            "analysis_markdown": text,
            "source": "gemini",
            "model": model_name,
            "latency_ms": int((time.perf_counter() - start_time) * 1000),
        }

    except HTTPError as e:
        # Attempt to read error body for better debugging
        error_body = e.read().decode('utf-8') if e.fp else "No details"
        logger.error(f"Gemini API HTTP {e.code}: {e.reason} | Body: {error_body}")
        
        return {
            "analysis_markdown": _fallback_advice(context, lang=lang),
            "source": "fallback_rules",
            "model": model_name,
            "error": f"HTTP {e.code}: {e.reason}",
        }
        
    except (URLError, Exception) as exc:
        logger.error(f"Gemini API connection failed: {exc}")
        return {
            "analysis_markdown": _fallback_advice(context, lang=lang),
            "source": "fallback_rules",
            "model": model_name,
            "error": str(exc),
        }