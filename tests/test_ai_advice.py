from app.config import Settings
from report.ai_advice import generate_ai_advice
from report.schema import ReportContext


def _sample_context() -> ReportContext:
    return ReportContext(
        as_of="2026-02-09",
        macro_events={
            "cpi_release": "2026-02-13",
            "nfp_release": "2026-02-07",
            "pmi_level": 52.4,
            "pmi_state": "expansion",
            "fomc_next_meeting": "2026-03-18",
            "event_risk_week": True,
        },
        rates={"yield_curve_slope": -0.3, "ten_year": 4.05, "two_year": 4.35},
        fedwatch={"probabilities": {"cut": 0.25, "hold": 0.55, "hike": 0.20}},
        cme_gap={"status": "gap_up", "gap": 150},
        derivatives={
            "funding_rate": 0.01,
            "funding_state": "neutral",
            "open_interest": 21_500_000_000,
            "open_interest_change_7d": -0.03,
            "open_interest_state": "stable",
        },
        stablecoin_flows={"net_flow_24h": -250_000_000, "net_flow_7d": 1_200_000_000},
    )


def test_generate_ai_advice_fallback_without_key():
    context = _sample_context()
    advice = generate_ai_advice(
        context,
        "# test",
        settings=Settings(openai_api_key=""),
    )
    assert advice["source"] == "fallback_rules"
    assert "Top Risks" in advice["analysis_markdown"]


class _FakeResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_ai_advice_openai_success(monkeypatch):
    context = _sample_context()
    payload = '{"output_text":"## AI\\n- Keep risk tight"}'

    def fake_urlopen(_req, timeout=30):
        assert timeout == 30
        return _FakeResponse(payload)

    monkeypatch.setattr("report.ai_advice.urlopen", fake_urlopen)

    advice = generate_ai_advice(
        context,
        "# test",
        settings=Settings(openai_api_key="test-key", openai_model="gpt-test"),
    )
    assert advice["source"] == "openai"
    assert advice["model"] == "gpt-test"
    assert "Keep risk tight" in advice["analysis_markdown"]
