"""Prompt templates for the weekly report."""

REPORT_TEMPLATE_EN = """# Macro + Crypto Weekly Brief

**As of:** {as_of}

## TL;DR
- CPI/NFP release timing may shift Fed expectations.
- Yield curve (10Y-2Y): {curve_slope:.2f}%
- Funding state: {funding_state}; OI state: {oi_state}
- Stablecoin exchange net flow (24h): {stablecoin_24h:,}

## Macro
- CPI release: {cpi_release}
- NFP release: {nfp_release}
- ISM Services PMI: {pmi_level} ({pmi_state})
- Next FOMC meeting: {fomc_meeting}

## Rates
- 10Y: {ten_year:.2f}%
- 2Y: {two_year:.2f}%
- 10Y-2Y: {curve_slope:.2f}%

## FedWatch
- Cut: {prob_cut:.0%}, Hold: {prob_hold:.0%}, Hike: {prob_hike:.0%}

## Crypto Derivatives
- Funding rate: {funding_rate:.3f}
- Open interest: {open_interest:,} (7d change: {oi_change:.0%})

## Stablecoin Flow
- 24h: {stablecoin_24h:,}
- 7d: {stablecoin_7d:,}

## CME Gap
- Status: {gap_status}
- Gap size: {gap_value:,}
"""

REPORT_TEMPLATE_ZH = """# 宏觀 + 加密 週報摘要

**資料時間：** {as_of}

## 重點摘要
- CPI/NFP 發布時點可能改變市場對 Fed 預期。
- 殖利率曲線（10Y-2Y）：{curve_slope:.2f}%
- 資金費率狀態：{funding_state}；OI 狀態：{oi_state}
- 穩定幣交易所 24h 淨流：{stablecoin_24h:,}

## 宏觀
- CPI 發布日：{cpi_release}
- NFP 發布日：{nfp_release}
- ISM 服務業 PMI：{pmi_level}（{pmi_state}）
- 下次 FOMC 會議：{fomc_meeting}

## 利率
- 10Y：{ten_year:.2f}%
- 2Y：{two_year:.2f}%
- 10Y-2Y：{curve_slope:.2f}%

## FedWatch
- 降息：{prob_cut:.0%}，維持：{prob_hold:.0%}，升息：{prob_hike:.0%}

## 衍生品
- Funding Rate：{funding_rate:.3f}
- 未平倉量：{open_interest:,}（7d 變化：{oi_change:.0%}）

## 穩定幣資金流
- 24h：{stablecoin_24h:,}
- 7d：{stablecoin_7d:,}

## CME 缺口
- 狀態：{gap_status}
- 缺口大小：{gap_value:,}
"""


def get_report_template(lang: str) -> str:
    if lang.lower().startswith("zh"):
        return REPORT_TEMPLATE_ZH
    return REPORT_TEMPLATE_EN
