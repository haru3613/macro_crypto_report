"""Prompt templates for the weekly report."""

REPORT_TEMPLATE_EN = """# Macro + Crypto Weekly Brief

**As of:** {as_of}

## TL;DR
- CPI/NFP release timing may shift Fed expectations.
- Yield curve (10Y-2Y): {curve_slope}%
- Funding state: {funding_state}; OI state: {oi_state}
- Stablecoin supply delta (24h): {stablecoin_24h}

## Macro
- CPI Headline YoY: {cpi_headline_yoy}% | Prev {cpi_headline_yoy_prev}% | Expected {cpi_headline_expected} (Released: {cpi_release})
- CPI Core YoY:    {cpi_core_yoy}% | Prev {cpi_core_yoy_prev}% | Expected {cpi_core_expected}
- NFP Payrolls: {nfp_payroll_change} | Prev {nfp_payroll_change_prev} | Expected {nfp_payroll_expected} (Released: {nfp_release})
- Unemployment: {nfp_unemployment_rate}% | Prev {nfp_unemployment_rate_prev}%
- ISM Services PMI: {pmi_level} | Prev {pmi_level_prev} | Expected {pmi_expected} ({pmi_state})
- Next FOMC meeting: {fomc_meeting}

## Rates
- 10Y: {ten_year}%
- 2Y: {two_year}%
- 10Y-2Y: {curve_slope}%

## FedWatch
- Cut: {prob_cut}, Hold: {prob_hold}, Hike: {prob_hike}

## Crypto Derivatives
- Funding rate: {funding_rate}
- Open interest: {open_interest} (7d change: {oi_change})

## Stablecoin Supply
- Total mcap: {stablecoin_total_mcap}
- 24h change: {stablecoin_24h}
- 7d change: {stablecoin_7d}

## CME Gap
- Status: {gap_status}
- Gap size: {gap_value}

## Prediction Markets *(market-derived, non-official)*
{polymarket_section}
"""

REPORT_TEMPLATE_ZH = """# 宏觀 + 加密 週報摘要

**資料時間：** {as_of}

## 重點摘要
- CPI/NFP 發布時點可能改變市場對 Fed 預期。
- 殖利率曲線（10Y-2Y）：{curve_slope}%
- 資金費率狀態：{funding_state}；OI 狀態：{oi_state}
- 穩定幣供給 24h 變化：{stablecoin_24h}

## 宏觀
- CPI 整體年增：{cpi_headline_yoy}% | 前值 {cpi_headline_yoy_prev}% | 預期 {cpi_headline_expected}（發布日：{cpi_release}）
- CPI 核心年增：{cpi_core_yoy}% | 前值 {cpi_core_yoy_prev}% | 預期 {cpi_core_expected}
- NFP 就業人數：{nfp_payroll_change} | 前值 {nfp_payroll_change_prev} | 預期 {nfp_payroll_expected}（發布日：{nfp_release}）
- 失業率：{nfp_unemployment_rate}% | 前值 {nfp_unemployment_rate_prev}%
- ISM 服務業 PMI：{pmi_level} | 前值 {pmi_level_prev} | 預期 {pmi_expected}（{pmi_state}）
- 下次 FOMC 會議：{fomc_meeting}

## 利率
- 10Y：{ten_year}%
- 2Y：{two_year}%
- 10Y-2Y：{curve_slope}%

## FedWatch
- 降息：{prob_cut}，維持：{prob_hold}，升息：{prob_hike}

## 衍生品
- Funding Rate：{funding_rate}
- 未平倉量：{open_interest}（7d 變化：{oi_change}）

## 穩定幣供給
- 總市值：{stablecoin_total_mcap}
- 24h 變化：{stablecoin_24h}
- 7d 變化：{stablecoin_7d}

## CME 缺口
- 狀態：{gap_status}
- 缺口大小：{gap_value}

## 預測市場 *（市場定價，非官方）*
{polymarket_section}
"""


def get_report_template(lang: str) -> str:
    if lang.lower().startswith("zh"):
        return REPORT_TEMPLATE_ZH
    return REPORT_TEMPLATE_EN
