from app.config import Settings
from conftest import FakeResponse, make_sample_context
from report.ai_advice import generate_ai_advice


def test_generate_ai_advice_fallback_without_key():
    context = make_sample_context()
    advice = generate_ai_advice(
        context,
        "# test",
        settings=Settings(openai_api_key=""),
    )
    assert advice["source"] == "fallback_rules"
    assert "Top Risks" in advice["analysis_markdown"]


def test_generate_ai_advice_openai_success(monkeypatch):
    context = make_sample_context()
    payload = '{"output_text":"## AI\\n- Keep risk tight"}'

    def fake_urlopen(_req, timeout=30):
        assert timeout == 30
        return FakeResponse(payload)

    monkeypatch.setattr("report.ai_advice.urlopen", fake_urlopen)

    advice = generate_ai_advice(
        context,
        "# test",
        settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
    )
    assert advice["source"] == "openai"
    assert advice["model"] == "gpt-test"
    assert "Keep risk tight" in advice["analysis_markdown"]
