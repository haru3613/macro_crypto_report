from conftest import make_sample_context
from report.ai_advice import generate_ai_advice


def test_generate_ai_advice_returns_rules_engine():
    context = make_sample_context()
    advice = generate_ai_advice(context, "# test")
    assert advice["source"] == "rules_engine"
    assert advice["model"] == "none"
    assert "Market Regime" in advice["analysis_markdown"] or "市場型態" in advice["analysis_markdown"]


def test_generate_ai_advice_zh():
    context = make_sample_context()
    advice = generate_ai_advice(context, "# test", lang="zh-TW")
    assert "市場型態" in advice["analysis_markdown"]
    assert "核心風險" in advice["analysis_markdown"]


def test_generate_ai_advice_en():
    context = make_sample_context()
    advice = generate_ai_advice(context, "# test", lang="en")
    assert "Market Regime" in advice["analysis_markdown"]
    assert "Top Risks" in advice["analysis_markdown"]
