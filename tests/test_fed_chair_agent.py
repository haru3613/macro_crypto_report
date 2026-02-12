"""Tests for the Fed Chair sub-agent."""

import pytest

from report.fed_chair_agent import (
    _hawkishness_score,
    _build_analysis,
    generate_fed_chair_analysis,
)
from tests.conftest import make_sample_context


# ── Hawkishness score ─────────────────────────────────────────────────────────

def test_hawkishness_score_high_inflation():
    """High CPI + tight labour -> score > 6 (hawkish territory)."""
    ctx = make_sample_context(
        macro_events_overrides={
            "cpi_headline_yoy": 4.5,
            "cpi_core_yoy": 4.2,
            "nfp_unemployment_rate": 3.5,
            "pmi_level": 53.0,
        }
    )
    score = _hawkishness_score(ctx)
    assert score >= 7


def test_hawkishness_score_low_inflation_weak_labour():
    """Low CPI + rising unemployment -> score <= 4 (dovish territory)."""
    ctx = make_sample_context(
        macro_events_overrides={
            "cpi_headline_yoy": 1.8,
            "cpi_core_yoy": 1.9,
            "nfp_unemployment_rate": 4.8,
            "pmi_level": 47.5,
        }
    )
    score = _hawkishness_score(ctx)
    assert score <= 4


def test_hawkishness_score_clamped():
    """Score must stay within 1-10."""
    ctx_hot = make_sample_context(
        macro_events_overrides={
            "cpi_headline_yoy": 9.0,
            "cpi_core_yoy": 8.0,
            "nfp_unemployment_rate": 3.0,
            "pmi_level": 60.0,
        }
    )
    ctx_cold = make_sample_context(
        macro_events_overrides={
            "cpi_headline_yoy": 0.5,
            "cpi_core_yoy": 0.8,
            "nfp_unemployment_rate": 6.0,
            "pmi_level": 40.0,
        }
    )
    assert 1 <= _hawkishness_score(ctx_hot) <= 10
    assert 1 <= _hawkishness_score(ctx_cold) <= 10


# ── Analysis output structure ────────────────────────────────────────────────

@pytest.mark.parametrize("lang", ["en", "zh-TW"])
def test_analysis_contains_all_sections(lang):
    ctx = make_sample_context()
    output = _build_analysis(ctx, lang=lang)
    if lang.startswith("zh"):
        required = [
            "政策立場", "鷹派評分",
            "雙重使命儀表板",
            "反應函數",
            "溝通風險",
            "市場下一步交易什麼",
            "引用來源",
        ]
    else:
        required = [
            "Policy Stance", "Hawkishness Score",
            "Dual Mandate Dashboard",
            "Reaction Function",
            "Communication Risk",
            "What Markets Will Trade Next",
            "Citations",
        ]
    for section in required:
        assert section in output, f"Missing section: {section!r}"


def test_analysis_contains_macro_values():
    ctx = make_sample_context()
    output = _build_analysis(ctx, lang="en")
    me = ctx.macro_events
    assert str(me["cpi_headline_yoy"]) in output
    assert str(me["nfp_unemployment_rate"]) in output


def test_analysis_labels_market_data():
    """FedWatch probabilities must be explicitly labelled as non-official."""
    ctx = make_sample_context()
    for lang in ("en", "zh-TW"):
        output = _build_analysis(ctx, lang=lang)
        assert "non-official" in output or "非官方" in output


# ── generate_fed_chair_analysis ──────────────────────────────────────────────

def test_generate_returns_rules_engine():
    ctx = make_sample_context()
    result = generate_fed_chair_analysis(ctx, "## brief", lang="en")
    assert result["source"] == "rules_engine"
    assert "hawkishness_score" in result
    assert isinstance(result["hawkishness_score"], int)
    assert "Policy Stance" in result["analysis_markdown"]


def test_generate_returns_hawkishness_score():
    ctx = make_sample_context()
    result = generate_fed_chair_analysis(ctx, "## brief", lang="zh-TW")
    assert 1 <= result["hawkishness_score"] <= 10
