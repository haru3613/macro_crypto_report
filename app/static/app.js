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
  { key: "CPI", labelZh: "CPI 消費者物價", labelEn: "CPI", kpiIds: [] },
  { key: "NFP", labelZh: "非農就業", labelEn: "NFP", kpiIds: [] },
  { key: "ISM PMI", labelZh: "ISM PMI", labelEn: "ISM PMI", kpiIds: [] },
  { key: "FOMC", labelZh: "FOMC 日程", labelEn: "FOMC Schedule", kpiIds: [] },
  { key: "FedWatch", labelZh: "FedWatch 機率", labelEn: "FedWatch Probabilities", kpiIds: ["fed-cut", "fed-hold", "fed-hike"] },
  { key: "CME OHLC", labelZh: "CME 缺口", labelEn: "CME Gap", kpiIds: ["cme-gap"] },
  { key: "Crypto Derivatives", labelZh: "加密衍生品", labelEn: "Crypto Derivatives", kpiIds: ["funding-state", "oi-state", "funding-rate", "oi-change"] },
  { key: "Stablecoin Flows", labelZh: "穩定幣流向", labelEn: "Stablecoin Flows", kpiIds: ["flow-24h"] },
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
    item.className = `source-status-item ${isPlaceholder ? "placeholder" : "live"}`;

    const label = currentLang === "zh-TW" ? src.labelZh : src.labelEn;
    const badgeText = isPlaceholder ? t("placeholderBadge") : t("liveBadge");
    const badgeClass = isPlaceholder ? "placeholder" : "live";
    const icon = isPlaceholder ? "\u26a0\ufe0f" : "\u2705";

    item.innerHTML = `<span>${icon}</span><span>${label}</span><span class="source-badge ${badgeClass}">${badgeText}</span>`;
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

async function loadWeeklyReport() {
  const status = byId("status");
  status.textContent = t("statusSyncing");

  try {
    const response = await fetch(`/report/weekly/advice?lang=${encodeURIComponent(qsLang())}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    const context = payload.context;

    byId("as-of").textContent = context.as_of;
    byId("curve-slope").textContent = `${context.rates.yield_curve_slope.toFixed(2)}%`;
    byId("cme-gap").textContent = `${mapLabel(context.cme_gap.status)} (${fmtNum(context.cme_gap.gap || 0)})`;
    byId("funding-state").textContent = mapLabel(context.derivatives.funding_state);
    byId("oi-state").textContent = mapLabel(context.derivatives.open_interest_state);
    byId("flow-24h").textContent = fmtNum(context.stablecoin_flows.net_flow_24h);

    byId("ten-year").textContent = `${context.rates.ten_year.toFixed(2)}%`;
    byId("two-year").textContent = `${context.rates.two_year.toFixed(2)}%`;
    byId("fed-cut").textContent = fmtPct(context.fedwatch.probabilities.cut, 0);
    byId("fed-hold").textContent = fmtPct(context.fedwatch.probabilities.hold, 0);
    byId("fed-hike").textContent = fmtPct(context.fedwatch.probabilities.hike, 0);
    byId("funding-rate").textContent = context.derivatives.funding_rate.toFixed(3);
    byId("oi-change").textContent = fmtPct(context.derivatives.open_interest_change_7d, 0);

    byId("report-markdown").textContent = payload.report_markdown;
    byId("ai-source").textContent = payload.ai_advice.source || "-";
    byId("ai-model").textContent = payload.ai_advice.model || "-";
    byId("ai-advice").textContent = payload.ai_advice.analysis_markdown || t("noAdvice");

    // Render data source status panel
    renderSourceStatus(context.placeholder_sources || []);

    const signalsResponse = await fetch("/signals/latest");
    if (!signalsResponse.ok) {
      throw new Error(`Signals HTTP ${signalsResponse.status}`);
    }
    const signalsPayload = await signalsResponse.json();

    const summary = payload.signals_summary || {};
    const sum15m = summary["15m"] || {};
    const sum1d = summary["1d"] || {};
    byId("sum-15m-buy").textContent = sum15m.buy ?? "-";
    byId("sum-15m-sell").textContent = sum15m.sell ?? "-";
    byId("sum-15m-hold").textContent = sum15m.hold ?? "-";
    byId("sum-1d-acc").textContent = sum1d.accumulate ?? "-";
    byId("sum-1d-red").textContent = sum1d.reduce ?? "-";
    byId("sum-1d-hold").textContent = sum1d.hold ?? "-";

    const previewLines = (signalsPayload.signals || []).slice(0, 12).map(formatSignalLine);
    byId("signals-preview").textContent = previewLines.join("\n\n") || t("noSignals");

    status.textContent = t("statusDone");
  } catch (error) {
    status.textContent = `${t("statusFailed")}: ${error.message}`;
  }
}

byId("lang-select").addEventListener("change", (event) => {
  currentLang = event.target.value;
  setI18nText();
  loadWeeklyReport();
});

byId("refresh-btn").addEventListener("click", loadWeeklyReport);
setI18nText();
loadWeeklyReport();
