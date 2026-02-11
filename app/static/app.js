function byId(id) {
  return document.getElementById(id);
}

const I18N = {
  "zh-TW": {
    eyebrow: "Macro + Crypto Signal Desk",
    title: "即時策略決策儀表板",
    subtitle: "以 /signals 與 /report 即時資料生成可執行建議",
    langLabel: "語言",
    refresh: "重新整理",
    marketPulse: "市場脈搏",
    asOf: "資料時間",
    curveSlope: "殖利率曲線 10Y-2Y",
    cmeGap: "CME 缺口",
    fundingState: "Funding 狀態",
    oiState: "OI 狀態",
    stablecoin24: "穩定幣 24h 淨流",
    macroData: "宏觀數據",
    econIndicators: "經濟指標",
    indicator: "指標",
    actual: "實際值",
    prev: "前值",
    expected: "預期",
    cpiHeadline: "CPI 整體 YoY",
    cpiCore: "CPI 核心 YoY",
    nfpPayroll: "NFP 就業人數",
    nfpUnrate: "失業率",
    cpiRelease: "CPI 發布日",
    nfpRelease: "NFP 發布日",
    fedSchedule: "Fed 行事曆",
    nextFomc: "下次 FOMC",
    pmiState: "ISM PMI 狀態",
    stablecoin7d: "穩定幣 7d 淨流",
    polymarketTitle: "預測市場",
    polymarketTag: "(市場定價，非官方)",
    polymarketQ: "合約問題",
    polymarketYes: "Yes",
    polymarketNo: "No",
    polymarketVol: "成交量",
    polymarketNone: "目前無活躍的宏觀預測合約。",
    signalSummary: "訊號總覽",
    m15Buy: "15m 買入",
    m15Sell: "15m 賣出",
    m15Hold: "15m 觀望",
    d1Acc: "1d 加碼",
    d1Reduce: "1d 減碼",
    d1Hold: "1d 觀望",
    ratesFedwatch: "利率與 FedWatch",
    cut: "降息",
    hold: "維持",
    hike: "升息",
    fundingRate: "Funding Rate",
    oiChange: "OI 7d 變化",
    signalsTitle: "最新可執行訊號",
    weeklyTitle: "週報內容",
    aiTitle: "AI 分析與建議",
    source: "來源",
    model: "模型",
    statusSyncing: "正在更新資料...",
    statusDone: "週報與訊號已更新。",
    statusFailed: "讀取失敗",
    noSignals: "目前沒有訊號。",
    noAdvice: "目前無 AI 建議。",
    sourceStatusTitle: "資料來源狀態",
    liveBadge: "Live",
    placeholderBadge: "假資料",
    placeholderWarning: "假資料",
    aiStart: "開始 AI 分析",
    aiLoading: "AI 分析中...",
    aiIdle: "點擊上方按鈕開始 AI 分析",
    aiFailed: "AI 分析失敗",
    fedChairTitle: "Fed Chair 政策分析",
    fedChairStart: "開始 Fed Chair 分析",
    fedChairLoading: "Fed Chair 分析中...",
    fedChairIdle: "點擊上方按鈕啟動 FOMC 雙重使命政策分析",
    fedChairFailed: "Fed Chair 分析失敗",
    hawkScore: "鷹派評分",
    expansion: "擴張",
    contraction: "收縮",
  },
  en: {
    eyebrow: "Macro + Crypto Signal Desk",
    title: "Live Strategy Dashboard",
    subtitle: "Actionable outputs from /signals and /report in real time",
    langLabel: "Language",
    refresh: "Refresh",
    marketPulse: "Market Pulse",
    asOf: "As Of",
    curveSlope: "Yield Curve 10Y-2Y",
    cmeGap: "CME Gap",
    fundingState: "Funding State",
    oiState: "OI State",
    stablecoin24: "Stablecoin Net 24h",
    macroData: "Macro Data",
    econIndicators: "Economic Indicators",
    indicator: "Indicator",
    actual: "Actual",
    prev: "Prev",
    expected: "Expected",
    cpiHeadline: "CPI Headline YoY",
    cpiCore: "CPI Core YoY",
    nfpPayroll: "NFP Payrolls",
    nfpUnrate: "Unemployment Rate",
    cpiRelease: "CPI Release",
    nfpRelease: "NFP Release",
    fedSchedule: "Fed Calendar",
    nextFomc: "Next FOMC",
    pmiState: "ISM PMI State",
    stablecoin7d: "Stablecoin Net 7d",
    polymarketTitle: "Prediction Markets",
    polymarketTag: "(market-derived, non-official)",
    polymarketQ: "Question",
    polymarketYes: "Yes",
    polymarketNo: "No",
    polymarketVol: "Volume",
    polymarketNone: "No active macro prediction markets found.",
    signalSummary: "Signal Summary",
    m15Buy: "15m Buy",
    m15Sell: "15m Sell",
    m15Hold: "15m Hold",
    d1Acc: "1d Accumulate",
    d1Reduce: "1d Reduce",
    d1Hold: "1d Hold",
    ratesFedwatch: "Rates + FedWatch",
    cut: "Cut",
    hold: "Hold",
    hike: "Hike",
    fundingRate: "Funding Rate",
    oiChange: "OI 7d Change",
    signalsTitle: "Latest Actionable Signals",
    weeklyTitle: "Weekly Report",
    aiTitle: "AI Analysis + Suggestions",
    source: "Source",
    model: "Model",
    statusSyncing: "Refreshing data...",
    statusDone: "Report and signals synced.",
    statusFailed: "Failed to load",
    noSignals: "No signals.",
    noAdvice: "No AI advice.",
    sourceStatusTitle: "Data Source Status",
    liveBadge: "Live",
    placeholderBadge: "Placeholder",
    placeholderWarning: "Placeholder",
    aiStart: "Run AI Analysis",
    aiLoading: "Analyzing...",
    aiIdle: "Click the button above to run AI analysis",
    aiFailed: "AI analysis failed",
    fedChairTitle: "Fed Chair Policy Analysis",
    fedChairStart: "Run Fed Chair Analysis",
    fedChairLoading: "Analyzing...",
    fedChairIdle: "Click the button above to run FOMC dual-mandate policy analysis",
    fedChairFailed: "Fed Chair analysis failed",
    hawkScore: "Hawk Score",
    expansion: "Expansion",
    contraction: "Contraction",
  },
};

const ACTION_LABEL = {
  "zh-TW": {
    buy: "買入",
    sell: "賣出",
    hold: "觀望",
    accumulate: "加碼",
    reduce: "減碼",
    expanding: "擴張",
    deleveraging: "去槓桿",
    stable: "穩定",
    overheated: "過熱",
    short_bias: "空方偏向",
    neutral: "中性",
    gap_up: "向上缺口",
    gap_down: "向下缺口",
    flat: "平盤",
  },
  en: {},
};

// All known data sources and which KPI elements they relate to
const ALL_SOURCES = [
  { key: "Yield Curve", labelZh: "殖利率曲線", labelEn: "Yield Curve", kpiIds: ["curve-slope", "ten-year", "two-year"] },
  { key: "CPI", labelZh: "CPI 消費者物價", labelEn: "CPI", kpiIds: ["cpi-headline", "cpi-core"] },
  { key: "NFP", labelZh: "非農就業", labelEn: "NFP", kpiIds: ["nfp-payroll", "nfp-unrate"] },
  { key: "ISM PMI", labelZh: "ISM PMI", labelEn: "ISM PMI", kpiIds: ["pmi-level"] },
  { key: "FOMC", labelZh: "FOMC 日程", labelEn: "FOMC Schedule", kpiIds: ["fomc-next"] },
  { key: "FedWatch", labelZh: "FedWatch 機率", labelEn: "FedWatch Probabilities", kpiIds: ["fed-cut", "fed-hold", "fed-hike"] },
  { key: "CME OHLC", labelZh: "CME 缺口", labelEn: "CME Gap", kpiIds: ["cme-gap"] },
  { key: "Crypto Derivatives", labelZh: "加密衍生品", labelEn: "Crypto Derivatives", kpiIds: ["funding-state", "oi-state", "funding-rate", "oi-change"] },
  { key: "Stablecoin Flows", labelZh: "穩定幣流向", labelEn: "Stablecoin Flows", kpiIds: ["flow-24h", "flow-7d"] },
  { key: "Polymarket", labelZh: "Polymarket 預測市場", labelEn: "Polymarket Predictions", kpiIds: [] },
  { key: "Finnhub Consensus", labelZh: "Finnhub 預期值", labelEn: "Finnhub Consensus", kpiIds: ["cpi-headline-exp", "cpi-core-exp", "nfp-payroll-exp", "pmi-level-exp"] },
];

let currentLang = "zh-TW";

function t(key) {
  const bundle = I18N[currentLang] || I18N.en;
  return bundle[key] || key;
}

function mapLabel(raw) {
  if (!raw) return "-";
  const key = String(raw).toLowerCase();
  return ACTION_LABEL[currentLang][key] || raw;
}

function fmtNum(value) {
  const locale = currentLang === "zh-TW" ? "zh-TW" : "en-US";
  return new Intl.NumberFormat(locale).format(value);
}

function fmtPct(value, digits = 2) {
  return `${(value * 100).toFixed(digits)}%`;
}

function setI18nText() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    // Skip ai-advice <pre> — its content is managed by loadAiAdvice()
    if (node.id === "ai-advice") return;
    const key = node.dataset.i18n;
    node.textContent = t(key);
  });
}

function qsLang() {
  return currentLang === "zh-TW" ? "zh-TW" : "en";
}

function formatSignalLine(signal) {
  return [
    `${signal.symbol} ${signal.timeframe} ${String(mapLabel(signal.action)).toUpperCase()} conf=${(signal.confidence * 100).toFixed(0)}%`,
    `entry=${signal.entry_low}~${signal.entry_high} stop=${signal.stop_loss} tp1=${signal.tp1} tp2=${signal.tp2}`,
    `size=${(signal.position_size_pct * 100).toFixed(2)}% quality=${signal.data_quality} invalidation=${signal.invalidation}`,
  ].join("\n");
}

function renderSourceStatus(placeholderSources) {
  const grid = byId("source-status-grid");
  grid.innerHTML = "";
  const placeholderSet = new Set(placeholderSources || []);

  ALL_SOURCES.forEach((src) => {
    const isPlaceholder = placeholderSet.has(src.key);
    const item = document.createElement("div");

    const baseCls = "flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-sm";
    if (isPlaceholder) {
      item.className = `${baseCls} border-amber-500/20 bg-amber-950/20 text-amber-300`;
    } else {
      item.className = `${baseCls} border-emerald-500/20 bg-emerald-950/20 text-emerald-300`;
    }

    const label = currentLang === "zh-TW" ? src.labelZh : src.labelEn;
    const badgeText = isPlaceholder ? t("placeholderBadge") : t("liveBadge");
    const icon = isPlaceholder ? "\u26a0\ufe0f" : "\u2705";

    const badgeCls = isPlaceholder
      ? "text-xs px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 font-semibold"
      : "text-xs px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-semibold";

    item.innerHTML = `<span>${icon}</span><span class="flex-1 text-slate-300">${label}</span><span class="${badgeCls}">${badgeText}</span>`;
    grid.appendChild(item);
  });

  // Add placeholder warning badges to KPI values
  document.querySelectorAll(".kpi-placeholder-badge").forEach((el) => el.remove());
  ALL_SOURCES.forEach((src) => {
    if (placeholderSet.has(src.key)) {
      src.kpiIds.forEach((id) => {
        const el = byId(id);
        if (el) {
          const badge = document.createElement("span");
          badge.className = "kpi-placeholder-badge";
          badge.textContent = ` \u26a0\ufe0f ${t("placeholderWarning")}`;
          el.parentNode.appendChild(badge);
        }
      });
    }
  });
}

// --- Helper: format expected value (null → N/A) ---
function fmtExpected(val) {
  return val == null ? "N/A" : String(val);
}

// --- Helper: render Polymarket table ---
function renderPolymarketTable(markets) {
  const container = byId("polymarket-table");
  if (!markets || markets.length === 0) {
    container.innerHTML = `<p class="text-xs text-slate-600">${t("polymarketNone")}</p>`;
    return;
  }
  let html = `<table class="w-full text-xs">
    <thead><tr class="text-xs text-slate-500 border-b border-slate-800/50">
      <th class="text-left py-1.5 font-medium">${t("polymarketQ")}</th>
      <th class="text-right py-1.5 font-medium">${t("polymarketYes")}</th>
      <th class="text-right py-1.5 font-medium">${t("polymarketNo")}</th>
      <th class="text-right py-1.5 font-medium">${t("polymarketVol")}</th>
    </tr></thead><tbody class="text-slate-300 font-mono">`;
  markets.forEach((m) => {
    const yes = m.outcomes?.Yes != null ? `${(m.outcomes.Yes * 100).toFixed(0)}%` : "—";
    const no = m.outcomes?.No != null ? `${(m.outcomes.No * 100).toFixed(0)}%` : "—";
    const vol = `$${fmtNum(m.volume_usd || 0)}`;
    // Truncate long questions for table display
    const q = (m.question || "").length > 55 ? m.question.substring(0, 52) + "..." : m.question;
    html += `<tr class="border-b border-slate-800/20">
      <td class="py-1.5 text-slate-400 font-sans">${q}</td>
      <td class="text-right py-1.5 text-emerald-400 font-semibold">${yes}</td>
      <td class="text-right py-1.5 text-rose-400">${no}</td>
      <td class="text-right py-1.5 text-slate-500">${vol}</td>
    </tr>`;
  });
  html += "</tbody></table>";
  container.innerHTML = html;
}

// --- AI section state management ---
function resetAiSection() {
  byId("ai-idle").classList.remove("hidden");
  byId("ai-output").classList.add("hidden");
  byId("ai-advice").textContent = "";
  byId("ai-source").textContent = "-";
  byId("ai-model").textContent = "-";
  const srcMobile = byId("ai-source-mobile");
  const modelMobile = byId("ai-model-mobile");
  if (srcMobile) srcMobile.textContent = "-";
  if (modelMobile) modelMobile.textContent = "-";
}

// --- Data loading (no AI) ---
async function loadDashboard() {
  const status = byId("status");
  status.textContent = t("statusSyncing");

  try {
    // Fetch report context + markdown (no AI call)
    const response = await fetch(`/report/weekly?lang=${encodeURIComponent(qsLang())}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const context = payload.context;

    const me = context.macro_events;

    // --- KPI Market Pulse ---
    byId("as-of").textContent = context.as_of;
    byId("curve-slope").textContent = `${context.rates.yield_curve_slope.toFixed(2)}%`;
    byId("cme-gap").textContent = `${mapLabel(context.cme_gap.status)} (${fmtNum(context.cme_gap.gap || 0)})`;
    byId("funding-state").textContent = mapLabel(context.derivatives.funding_state);
    byId("oi-state").textContent = mapLabel(context.derivatives.open_interest_state);
    byId("flow-24h").textContent = fmtNum(context.stablecoin_flows.net_flow_24h);

    // --- Macro Data: CPI / NFP / PMI ---
    byId("cpi-headline").textContent = `${me.cpi_headline_yoy}%`;
    byId("cpi-headline-prev").textContent = `${me.cpi_headline_yoy_prev}%`;
    byId("cpi-headline-exp").textContent = fmtExpected(me.cpi_headline_yoy_expected);
    byId("cpi-core").textContent = `${me.cpi_core_yoy}%`;
    byId("cpi-core-prev").textContent = `${me.cpi_core_yoy_prev}%`;
    byId("cpi-core-exp").textContent = fmtExpected(me.cpi_core_yoy_expected);
    byId("nfp-payroll").textContent = `${me.nfp_payroll_change >= 0 ? "+" : ""}${fmtNum(me.nfp_payroll_change)}`;
    byId("nfp-payroll-prev").textContent = `${me.nfp_payroll_change_prev >= 0 ? "+" : ""}${fmtNum(me.nfp_payroll_change_prev)}`;
    byId("nfp-payroll-exp").textContent = fmtExpected(me.nfp_payroll_change_expected);
    byId("nfp-unrate").textContent = `${me.nfp_unemployment_rate}%`;
    byId("nfp-unrate-prev").textContent = `${me.nfp_unemployment_rate_prev}%`;
    byId("pmi-level").textContent = me.pmi_level;
    byId("pmi-level-prev").textContent = me.pmi_level_prev;
    byId("pmi-level-exp").textContent = fmtExpected(me.pmi_level_expected);
    byId("cpi-release").textContent = me.cpi_release || "-";
    byId("nfp-release").textContent = me.nfp_release || "-";

    // --- FOMC + Stablecoin 7d ---
    byId("fomc-next").textContent = me.fomc_next_meeting || "-";
    const pmiStateLabel = me.pmi_state === "expansion" ? t("expansion") : t("contraction");
    const pmiStateEl = byId("pmi-state");
    pmiStateEl.textContent = pmiStateLabel;
    pmiStateEl.className = `font-mono text-sm ${me.pmi_state === "expansion" ? "text-emerald-400" : "text-rose-400"}`;
    byId("flow-7d").textContent = fmtNum(context.stablecoin_flows.net_flow_7d);

    // --- Polymarket ---
    renderPolymarketTable(context.polymarket_markets || []);

    // --- Rates + FedWatch ---
    byId("ten-year").textContent = `${context.rates.ten_year.toFixed(2)}%`;
    byId("two-year").textContent = `${context.rates.two_year.toFixed(2)}%`;
    byId("fed-cut").textContent = fmtPct(context.fedwatch.probabilities.cut, 0);
    byId("fed-hold").textContent = fmtPct(context.fedwatch.probabilities.hold, 0);
    byId("fed-hike").textContent = fmtPct(context.fedwatch.probabilities.hike, 0);
    byId("funding-rate").textContent = context.derivatives.funding_rate.toFixed(3);
    byId("oi-change").textContent = fmtPct(context.derivatives.open_interest_change_7d, 0);

    byId("report-markdown").textContent = payload.report_markdown;

    // Render data source status panel
    renderSourceStatus(context.placeholder_sources || []);

    // Fetch signals
    const signalsResponse = await fetch("/signals/latest");
    if (!signalsResponse.ok) throw new Error(`Signals HTTP ${signalsResponse.status}`);
    const signalsPayload = await signalsResponse.json();

    const signals = signalsPayload.signals || [];
    const sum15m = { buy: 0, sell: 0, hold: 0 };
    const sum1d = { accumulate: 0, reduce: 0, hold: 0 };
    signals.forEach((s) => {
      if (s.timeframe === "15m" && s.action in sum15m) sum15m[s.action]++;
      if (s.timeframe === "1d" && s.action in sum1d) sum1d[s.action]++;
    });
    byId("sum-15m-buy").textContent = sum15m.buy;
    byId("sum-15m-sell").textContent = sum15m.sell;
    byId("sum-15m-hold").textContent = sum15m.hold;
    byId("sum-1d-acc").textContent = sum1d.accumulate;
    byId("sum-1d-red").textContent = sum1d.reduce;
    byId("sum-1d-hold").textContent = sum1d.hold;

    const previewLines = signals.slice(0, 12).map(formatSignalLine);
    byId("signals-preview").textContent = previewLines.join("\n\n") || t("noSignals");

    status.textContent = t("statusDone");
  } catch (error) {
    status.textContent = `${t("statusFailed")}: ${error.message}`;
  }
}

// --- AI analysis (on-demand only, never called automatically) ---
async function loadAiAdvice() {
  const btn = byId("ai-btn");
  const pre = byId("ai-advice");
  const idleDiv = byId("ai-idle");
  const outputDiv = byId("ai-output");

  btn.disabled = true;
  btn.textContent = t("aiLoading");

  // Switch from idle to output view
  idleDiv.classList.add("hidden");
  outputDiv.classList.remove("hidden");
  pre.textContent = t("aiLoading");
  byId("ai-source").textContent = "-";
  byId("ai-model").textContent = "-";
  const srcMobile = byId("ai-source-mobile");
  const modelMobile = byId("ai-model-mobile");
  if (srcMobile) srcMobile.textContent = "-";
  if (modelMobile) modelMobile.textContent = "-";

  try {
    const response = await fetch(`/report/weekly/ai?lang=${encodeURIComponent(qsLang())}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const advice = await response.json();

    byId("ai-source").textContent = advice.source || "-";
    byId("ai-model").textContent = advice.model || "-";
    if (srcMobile) srcMobile.textContent = advice.source || "-";
    if (modelMobile) modelMobile.textContent = advice.model || "-";
    pre.textContent = advice.analysis_markdown || t("noAdvice");
  } catch (error) {
    pre.textContent = `${t("aiFailed")}: ${error.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = t("aiStart");
  }
}

// --- Fed Chair analysis (on-demand) ---
function resetFedChairSection() {
  byId("fed-chair-idle").classList.remove("hidden");
  byId("fed-chair-output").classList.add("hidden");
  byId("fed-chair-advice").textContent = "";
  byId("fed-hawk-score").textContent = "-";
  byId("fed-source").textContent = "-";
  const scoreMobile = byId("fed-hawk-score-mobile");
  const srcMobile = byId("fed-source-mobile");
  if (scoreMobile) scoreMobile.textContent = "-";
  if (srcMobile) srcMobile.textContent = "-";
}

async function loadFedChairAnalysis() {
  const btn = byId("fed-chair-btn");
  const pre = byId("fed-chair-advice");
  const idleDiv = byId("fed-chair-idle");
  const outputDiv = byId("fed-chair-output");

  btn.disabled = true;
  btn.textContent = t("fedChairLoading");

  idleDiv.classList.add("hidden");
  outputDiv.classList.remove("hidden");
  pre.textContent = t("fedChairLoading");

  try {
    const response = await fetch(`/report/weekly/fed-chair?lang=${encodeURIComponent(qsLang())}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const analysis = payload.fed_chair_analysis || {};

    pre.textContent = analysis.analysis_markdown || "";
    byId("fed-hawk-score").textContent = analysis.hawkishness_score ?? "-";
    byId("fed-source").textContent = analysis.source || "-";
    const scoreMobile = byId("fed-hawk-score-mobile");
    const srcMobile = byId("fed-source-mobile");
    if (scoreMobile) scoreMobile.textContent = analysis.hawkishness_score ?? "-";
    if (srcMobile) srcMobile.textContent = analysis.source || "-";
  } catch (error) {
    pre.textContent = `${t("fedChairFailed")}: ${error.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = t("fedChairStart");
  }
}

byId("lang-select").addEventListener("change", (event) => {
  currentLang = event.target.value;
  setI18nText();
  resetAiSection();
  resetFedChairSection();
  loadDashboard();
});

byId("refresh-btn").addEventListener("click", loadDashboard);
byId("ai-btn").addEventListener("click", loadAiAdvice);
byId("fed-chair-btn").addEventListener("click", loadFedChairAnalysis);
setI18nText();
loadDashboard();
