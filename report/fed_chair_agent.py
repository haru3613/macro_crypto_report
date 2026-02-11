"""Fed Chair (Powell-style) Sub-Agent.

Interprets latest macro data through the FOMC dual-mandate framework and
outputs a structured policy-stance analysis. Only official sources are used
as primary evidence; market pricing is labelled explicitly as market-derived.

Output sections (fixed):
  1. Policy Stance + Hawkishness Score
  2. Dual Mandate Dashboard
  3. Reaction Function (if / then)
  4. Communication Risk
  5. What Markets Will Trade Next
  6. Citations
"""

import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

from app.config import Settings, get_settings
from report.schema import ReportContext

# ── Fed target constants ──────────────────────────────────────────────────────
_PCE_TARGET = 2.0          # FOMC symmetric 2% PCE inflation target
_NAIRU = 4.0               # Long-run neutral unemployment (SEP median, approx.)
_NEUTRAL_RATE = 2.5        # Long-run nominal neutral rate (SEP long-run dot)

# ── Gemini ────────────────────────────────────────────────────────────────────
_GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

_SYSTEM_PROMPT_EN = """\
You are the Federal Reserve Chair conducting an internal policy briefing.
Apply the FOMC dual-mandate framework (price stability at 2% PCE + maximum
employment) to the structured macro data provided.

STRICT RULES:
- Use only official sources as primary evidence:
  FOMC statements / SEP / minutes / press-conference transcripts /
  Fed Governor speeches / FRED data series / BLS releases / BEA releases.
- Market-derived data (FedWatch probabilities, futures pricing) must be
  clearly labelled as "(market-derived, non-official)".
- Do NOT make price predictions or investment recommendations.
- Output ONLY the six sections below, in order, using the exact headers.

OUTPUT FORMAT (markdown):

## 1. Policy Stance
[Current stance: one of Tightening / Hold / Easing / Data-Dependent Hold]
**Hawkishness Score: X / 10** (1 = maximally dovish, 10 = maximally hawkish)
[2–3 sentence rationale grounded in mandate gaps]

## 2. Dual Mandate Dashboard
| Indicator | Latest | Target / Threshold | Gap | Mandate Pressure |
|---|---|---|---|---|
| CPI Headline YoY | ... | 2.0% PCE proxy | ... | ... |
| CPI Core YoY | ... | 2.0% PCE proxy | ... | ... |
| NFP Payrolls (MoM) | ... | ~100–150k sustainable | ... | ... |
| Unemployment Rate | ... | ~4.0% NAIRU | ... | ... |
| ISM Services PMI | ... | 50 neutral | ... | ... |

## 3. Reaction Function
**Price Stability path:**
- IF [condition] → THEN [policy response]
- IF [condition] → THEN [policy response]

**Employment path:**
- IF [condition] → THEN [policy response]
- IF [condition] → THEN [policy response]

## 4. Communication Risk
[Risk of market misreading Fed messaging; cite any divergence between
dot-plot / statement language and current market pricing. Label all
market pricing as (market-derived, non-official).]

## 5. What Markets Will Trade Next
[Next 1–2 data catalysts that could shift Fed's reaction function.
No price forecasts — describe the conditional impact only.]

## 6. Citations
[List official sources used: FRED series IDs, BLS release dates, FOMC
statement date / SEP vintage, Fed speech titles and dates.]
"""

_SYSTEM_PROMPT_ZH = """\
你是美聯儲主席，正在主持一場內部政策簡報。
依據 FOMC 雙重使命框架（物價穩定目標 PCE 2% + 充分就業）解讀提供的宏觀資料。

嚴格規則：
- 僅以官方來源作為主要依據：
  FOMC 聲明 / SEP（季度經濟預測摘要）/ 會議記錄 / 記者會逐字稿 /
  理事演講 / FRED 資料系列 / BLS 發布 / BEA 發布。
- 市場衍生數據（FedWatch 機率、期貨定價）必須明確標示為「（市場定價，非官方）」。
- 不做價格預測，不做投資建議。
- 僅輸出以下六個區塊，依序排列，使用完全相同的標題。

輸出格式（markdown）：

## 1. 政策立場
[當前立場：緊縮 / 按兵不動 / 寬鬆 / 數據依賴的按兵不動 之一]
**鷹派評分：X / 10**（1 = 最鴿，10 = 最鷹）
[2–3 句依據使命缺口的理由]

## 2. 雙重使命儀表板
| 指標 | 最新值 | 目標 / 門檻 | 缺口 | 使命壓力 |
|---|---|---|---|---|
| CPI 整體年增 | ... | PCE 代理 2.0% | ... | ... |
| CPI 核心年增 | ... | PCE 代理 2.0% | ... | ... |
| NFP 非農就業（月增） | ... | 可持續約 10–15 萬 | ... | ... |
| 失業率 | ... | NAIRU 約 4.0% | ... | ... |
| ISM 服務業 PMI | ... | 50 中性 | ... | ... |

## 3. 反應函數
**物價穩定路徑：**
- 若 [條件] → 則 [政策回應]
- 若 [條件] → 則 [政策回應]

**就業路徑：**
- 若 [條件] → 則 [政策回應]
- 若 [條件] → 則 [政策回應]

## 4. 溝通風險
[市場誤讀 Fed 訊號的風險；引用點陣圖 / 聲明措辭與當前市場定價的偏差。
所有市場定價需標示為（市場定價，非官方）。]

## 5. 市場下一步交易什麼
[未來 1–2 個能改變 Fed 反應函數的資料催化劑。
不做價格預測——僅描述條件式影響。]

## 6. 引用來源
[列出使用的官方來源：FRED 系列代碼、BLS 發布日期、FOMC 聲明日期 / SEP
版本、Fed 演講標題與日期。]
"""


# ── Hawkishness score (rules-based) ──────────────────────────────────────────

def _hawkishness_score(context: ReportContext) -> int:
    """Compute a 1–10 hawkishness score from mandate gap signals.

    Scale:
      1–3  Dovish  — significant labour weakness or inflation at/below target
      4–6  Neutral — data-dependent hold territory
      7–10 Hawkish — inflation persistently above target / labour market tight
    """
    score = 5  # baseline neutral

    me = context.macro_events
    headline = me.get("cpi_headline_yoy", _PCE_TARGET)
    core = me.get("cpi_core_yoy", _PCE_TARGET)
    unemployment = me.get("nfp_unemployment_rate", _NAIRU)
    pmi = me.get("pmi_level", 50.0)
    curve_slope = context.rates.get("yield_curve_slope", 0.0)

    # ── Inflation gap (above 2% is hawkish, below is dovish) ─────────────────
    headline_gap = headline - _PCE_TARGET
    if headline_gap > 2.0:
        score += 3
    elif headline_gap > 1.0:
        score += 2
    elif headline_gap > 0.5:
        score += 1
    elif headline_gap < -0.5:
        score -= 1

    # Core stickiness bonus
    if core > headline:
        score += 1

    # ── Labour market gap (below NAIRU = tight = hawkish) ────────────────────
    unemployment_gap = unemployment - _NAIRU
    if unemployment_gap < -0.5:
        score += 1   # labour still very tight
    elif unemployment_gap > 0.5:
        score -= 1   # slack emerging, dovish tilt
    elif unemployment_gap > 1.0:
        score -= 2

    # ── Activity signal ───────────────────────────────────────────────────────
    if pmi > 52:
        score += 1
    elif pmi < 48:
        score -= 1

    # ── Financial conditions (deeply inverted curve → tighter de facto) ───────
    if curve_slope < -0.5:
        score -= 1   # financial conditions already tight, less need to hike

    return max(1, min(10, score))


# ── Fallback (rules-based output) ────────────────────────────────────────────

def _stance_label(score: int, lang: str) -> str:
    if lang.lower().startswith("zh"):
        if score >= 8:
            return "緊縮"
        if score >= 6:
            return "數據依賴的按兵不動（鷹派偏向）"
        if score >= 4:
            return "數據依賴的按兵不動"
        return "寬鬆偏向"
    if score >= 8:
        return "Tightening"
    if score >= 6:
        return "Data-Dependent Hold (hawkish lean)"
    if score >= 4:
        return "Data-Dependent Hold"
    return "Easing Bias"


def _mandate_pressure(gap: float, direction: str = "above") -> str:
    """Return a pressure label given a gap value."""
    if direction == "above":
        if gap > 1.0:
            return "🔴 High hawkish"
        if gap > 0.3:
            return "🟡 Moderate hawkish"
        if gap < -0.3:
            return "🟢 Dovish / at target"
        return "🟢 Near target"
    # direction == "tight" (for unemployment below NAIRU)
    if gap < -0.5:
        return "🔴 Tight / hawkish"
    if gap < 0:
        return "🟡 Slightly tight"
    if gap > 0.5:
        return "🟢 Slack / dovish"
    return "🟢 Near NAIRU"


def _fallback_fed_chair(context: ReportContext, lang: str = "en") -> str:
    me = context.macro_events
    score = _hawkishness_score(context)
    stance = _stance_label(score, lang)

    headline = me.get("cpi_headline_yoy", 0.0)
    headline_prev = me.get("cpi_headline_yoy_prev", 0.0)
    core = me.get("cpi_core_yoy", 0.0)
    core_prev = me.get("cpi_core_yoy_prev", 0.0)
    payroll = me.get("nfp_payroll_change", 0)
    payroll_prev = me.get("nfp_payroll_change_prev", 0)
    unemp = me.get("nfp_unemployment_rate", 0.0)
    unemp_prev = me.get("nfp_unemployment_rate_prev", 0.0)
    pmi = me.get("pmi_level", 50.0)
    pmi_prev = me.get("pmi_level_prev", 50.0)
    fomc_next = me.get("fomc_next_meeting", "TBD")
    cpi_release = me.get("cpi_release", "N/A")
    nfp_release = me.get("nfp_release", "N/A")

    ten_year = context.rates.get("ten_year", 0.0)
    two_year = context.rates.get("two_year", 0.0)
    curve_slope = context.rates.get("yield_curve_slope", 0.0)

    prob_cut = context.fedwatch["probabilities"].get("cut", 0.0)
    prob_hold = context.fedwatch["probabilities"].get("hold", 0.0)
    prob_hike = context.fedwatch["probabilities"].get("hike", 0.0)

    h_gap = round(headline - _PCE_TARGET, 1)
    c_gap = round(core - _PCE_TARGET, 1)
    u_gap = round(unemp - _NAIRU, 1)
    pmi_gap = round(pmi - 50.0, 1)

    h_pressure = _mandate_pressure(h_gap, "above")
    c_pressure = _mandate_pressure(c_gap, "above")
    u_pressure = _mandate_pressure(u_gap, "tight")
    pmi_pressure = "🔴 Hot" if pmi > 52 else ("🟢 Cooling" if pmi < 48 else "🟢 Neutral")
    payroll_label = (
        "🔴 Hot" if payroll > 200_000
        else ("🟡 Solid" if payroll > 100_000 else "🟢 Cooling")
    )

    if lang.lower().startswith("zh"):
        return f"""\
## 1. 政策立場
當前立場：**{stance}**
**鷹派評分：{score} / 10**
CPI 整體年增 {headline:.1f}%（前值 {headline_prev:.1f}%），距 2% PCE 目標差距 {h_gap:+.1f}%。\
核心通膨 {core:.1f}%{'高於整體，黏性仍存' if core > headline else '，與整體接近'}。\
失業率 {unemp:.1f}%（{'低於' if unemp < _NAIRU else '高於'} NAIRU {_NAIRU:.1f}%），\
勞動市場{'仍偏緊' if unemp < _NAIRU else '略顯鬆動'}。\
雙重使命{'均指向維持限制性利率' if score >= 6 else '存在分歧，政策路徑需視後續數據'}。

## 2. 雙重使命儀表板
| 指標 | 最新值 | 前值 | 目標 / 門檻 | 缺口 | 使命壓力 |
|---|---|---|---|---|---|
| CPI 整體年增 | {headline:.1f}% | {headline_prev:.1f}% | PCE 代理 2.0% | {h_gap:+.1f}% | {h_pressure} |
| CPI 核心年增 | {core:.1f}% | {core_prev:.1f}% | PCE 代理 2.0% | {c_gap:+.1f}% | {c_pressure} |
| NFP 非農就業（月增） | {payroll:+,} | {payroll_prev:+,} | 可持續 10–15 萬 | — | {payroll_label} |
| 失業率 | {unemp:.1f}% | {unemp_prev:.1f}% | NAIRU ≈ 4.0% | {u_gap:+.1f}% | {u_pressure} |
| ISM 服務業 PMI | {pmi} | {pmi_prev} | 50 中性 | {pmi_gap:+.1f} | {pmi_pressure} |
| 10Y 公債殖利率 | {ten_year:.2f}% | — | — | — | — |
| 殖利率曲線（10Y-2Y） | {curve_slope:+.2f}% | — | 正斜率為健康 | — | {'🔴 倒掛' if curve_slope < 0 else '🟢 正斜率'} |

## 3. 反應函數
**物價穩定路徑：**
- 若 CPI 核心年增連續三個月 > 2.5% → 則暫停降息，重新評估限制性利率是否足夠
- 若 CPI 整體年增降至 2.0–2.5% 且核心同步回落 → 則為進一步調降提供空間
- 若通膨預期（5Y5Y breakeven）明顯上升 → 則鷹派措辭將重新回歸 FOMC 聲明

**就業路徑：**
- 若非農就業連續兩個月 < 75,000 或失業率突破 4.5% → 則加速降息討論
- 若失業率持平於 {unemp:.1f}% 而通膨未降 → 則維持現行限制性立場，按兵不動

## 4. 溝通風險
FedWatch 定價（市場定價，非官方）顯示：降息機率 {prob_cut:.0%} / 維持 {prob_hold:.0%} / 升息 {prob_hike:.0%}。\
{'市場預期降息與 FOMC 目前「數據依賴」措辭存在落差，若後續 CPI 意外偏高，可能引發利率市場重新定價。' if prob_cut > 0.3 else '市場定價與 Fed 偏中性立場大致吻合，溝通風險偏低；但若就業數據顯著惡化，鴿派轉向速度可能快於點陣圖暗示。'}
殖利率曲線目前{'倒掛' if curve_slope < 0 else '轉正'}（{curve_slope:+.2f}%），\
{'顯示市場預期未來政策寬鬆，但 Fed 尚未給出明確訊號。' if curve_slope < 0 else '金融條件邊際改善。'}

## 5. 市場下一步交易什麼
- **下次 CPI（{cpi_release}）**：若整體或核心意外高於前值，市場將重新推遲降息預期；若雙雙降溫則加速降息交易。
- **下次 NFP（{nfp_release}）**：若就業人數 < 100,000 或失業率破 4.5%，鴿派解讀主導；若 > 200,000 且薪資加速，鷹派反應。
- **下次 FOMC（{fomc_next}）**：聲明措辭調整（移除 / 加入「限制性」、「進一步進展」等關鍵詞）是主要催化劑。

## 6. 引用來源
- **FRED 資料**：CPIAUCSL（CPI 整體）、CPILFESL（CPI 核心）、PAYEMS（非農就業水準）、UNRATE（失業率）、DGS10、DGS2
- **ISM 服務業 PMI**：ISM 發布（Placeholder，NAPM 系列已停更）
- **FOMC 行事曆**：靜態 2025–2026 會議日期（來源：federalreserve.gov）
- **FedWatch 機率**：CME FedWatch（市場定價，非官方）
- 注意：所有 CPI 數據為 BLS FRED 代理值；嚴格比較須使用 BEA PCE 發布。"""

    # ── English ───────────────────────────────────────────────────────────────
    return f"""\
## 1. Policy Stance
Current stance: **{stance}**
**Hawkishness Score: {score} / 10**
CPI headline YoY at {headline:.1f}% (prev {headline_prev:.1f}%), \
{h_gap:+.1f}% above the 2% PCE proxy target. \
Core inflation at {core:.1f}%{'—above headline, suggesting stickiness' if core > headline else '—tracking close to headline'}. \
Unemployment at {unemp:.1f}% ({'below' if unemp < _NAIRU else 'above'} NAIRU {_NAIRU:.1f}%), \
labour market {'remains tight' if unemp < _NAIRU else 'showing modest slack'}. \
Dual-mandate signals {'both point to maintaining restrictive rates' if score >= 6 else 'are diverging; path depends on incoming data'}.

## 2. Dual Mandate Dashboard
| Indicator | Latest | Prev | Target / Threshold | Gap | Mandate Pressure |
|---|---|---|---|---|---|
| CPI Headline YoY | {headline:.1f}% | {headline_prev:.1f}% | 2.0% PCE proxy | {h_gap:+.1f}% | {h_pressure} |
| CPI Core YoY | {core:.1f}% | {core_prev:.1f}% | 2.0% PCE proxy | {c_gap:+.1f}% | {c_pressure} |
| NFP Payrolls (MoM) | {payroll:+,} | {payroll_prev:+,} | ~100–150k sustainable | — | {payroll_label} |
| Unemployment Rate | {unemp:.1f}% | {unemp_prev:.1f}% | ~4.0% NAIRU | {u_gap:+.1f}% | {u_pressure} |
| ISM Services PMI | {pmi} | {pmi_prev} | 50 neutral | {pmi_gap:+.1f} | {pmi_pressure} |
| 10Y Treasury Yield | {ten_year:.2f}% | — | — | — | — |
| Yield Curve (10Y-2Y) | {curve_slope:+.2f}% | — | Positive = healthy | — | {'🔴 Inverted' if curve_slope < 0 else '🟢 Positive'} |

## 3. Reaction Function
**Price stability path:**
- IF core CPI stays above 2.5% for 3+ months → THEN pause cuts, re-assess whether policy is sufficiently restrictive
- IF headline + core both trend toward 2.0–2.5% → THEN further cuts become appropriate
- IF 5Y5Y inflation breakeven rises materially → THEN hawkish language returns to FOMC statement

**Employment path:**
- IF NFP < 75k for two consecutive months OR unemployment breaches 4.5% → THEN accelerate easing discussion
- IF unemployment holds near {unemp:.1f}% while inflation stays elevated → THEN maintain current restrictive stance, no change

## 4. Communication Risk
FedWatch pricing (market-derived, non-official): Cut {prob_cut:.0%} / Hold {prob_hold:.0%} / Hike {prob_hike:.0%}. \
{'Market is pricing meaningful cut probability against FOMC’s "data-dependent" language—a CPI upside surprise could force rapid repricing.' if prob_cut > 0.3 else 'Market pricing broadly aligned with a neutral Fed posture; risk is a faster-than-expected dovish pivot if labour data deteriorates sharply.'} \
Yield curve currently {"inverted" if curve_slope < 0 else "positive"} ({curve_slope:+.2f}%), \
{"suggesting markets anticipate easing ahead of any explicit Fed signal." if curve_slope < 0 else "a marginal improvement in financial conditions."}

## 5. What Markets Will Trade Next
- **Next CPI ({cpi_release})**: A surprise above prev headline/core re-prices cuts further out; dual deceleration opens the door to an earlier cut.
- **Next NFP ({nfp_release})**: Payrolls < 100k or unemployment > 4.5% triggers dovish repricing; > 200k with wage acceleration = hawkish.
- **Next FOMC ({fomc_next})**: Statement language shifts (removal/addition of "restrictive", "further progress") are the primary catalyst.

## 6. Citations
- **FRED series**: CPIAUCSL (CPI Headline), CPILFESL (CPI Core), PAYEMS (Non-farm payrolls level), UNRATE, DGS10, DGS2
- **ISM Services PMI**: ISM release (Placeholder — NAPM series discontinued on FRED)
- **FOMC calendar**: Static 2025–2026 meeting dates (source: federalreserve.gov)
- **FedWatch probabilities**: CME FedWatch (market-derived, non-official)
- Note: All CPI figures are BLS/FRED proxy values; strict mandate analysis requires BEA PCE release."""


# ── Gemini call ───────────────────────────────────────────────────────────────

def _build_user_message(context: ReportContext, report_markdown: str, lang: str) -> str:
    return (
        f"Language preference: {lang}\n\n"
        "Structured macro context (JSON):\n"
        f"{json.dumps(context.model_dump(), ensure_ascii=True)}\n\n"
        "Weekly markdown brief for reference:\n"
        f"{report_markdown}"
    )


def generate_fed_chair_analysis(
    context: ReportContext,
    report_markdown: str,
    lang: str = "en",
    settings: Settings | None = None,
) -> dict:
    """Run the Fed Chair sub-agent. Returns a dict with analysis_markdown + metadata."""
    settings = settings or get_settings()

    if not settings.gemini_api_key:
        return {
            "analysis_markdown": _fallback_fed_chair(context, lang=lang),
            "source": "fallback_rules",
            "model": "none",
            "hawkishness_score": _hawkishness_score(context),
        }

    system_prompt = (
        _SYSTEM_PROMPT_ZH if lang.lower().startswith("zh") else _SYSTEM_PROMPT_EN
    )
    url = (
        _GEMINI_API_URL.format(model=settings.gemini_model)
        + "?"
        + urlencode({"key": settings.gemini_api_key})
    )
    request_body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {"parts": [{"text": _build_user_message(context, report_markdown, lang)}]}
        ],
        "generationConfig": {
            "temperature": 0.1,   # Low temperature: policy analysis demands consistency
            "maxOutputTokens": 1200,
        },
    }

    try:
        req = Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        candidates = payload.get("candidates", [])
        if not candidates:
            raise ValueError("Empty candidates in Gemini response")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts if p.get("text")).strip()
        if not text:
            raise ValueError("Empty text in Gemini response")

        return {
            "analysis_markdown": text,
            "source": "gemini",
            "model": settings.gemini_model,
            "hawkishness_score": _hawkishness_score(context),
        }
    except Exception as exc:
        logger.error("Gemini Fed Chair call failed, falling back to rules: %s", exc)
        return {
            "analysis_markdown": _fallback_fed_chair(context, lang=lang),
            "source": "fallback_rules",
            "model": settings.gemini_model,
            "error": str(exc),
            "hawkishness_score": _hawkishness_score(context),
        }
