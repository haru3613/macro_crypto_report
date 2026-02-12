"""API routes for weekly report generation."""

from typing import Literal

from fastapi import APIRouter
from fastapi import Query

from data.fetch_all import fetch_all_sources
from indicators.compute import compute_report_context
from report.ai_advice import generate_ai_advice
from report.fed_chair_agent import generate_fed_chair_analysis
from report.render import render_report
from services.signal_service import get_signal_service
from signals.summary import summarize_signals

router = APIRouter()


def _build_weekly_payload(lang: str) -> tuple:
    raw_data = fetch_all_sources()
    context = compute_report_context(raw_data)
    markdown = render_report(context, lang=lang)
    return context, markdown


@router.get("/weekly")
def weekly_report(lang: Literal["en", "zh-TW"] = Query(default="zh-TW")) -> dict:
    context, markdown = _build_weekly_payload(lang=lang)
    return {
        "context": context.model_dump(),
        "report_markdown": markdown,
    }


@router.get("/weekly/advice")
def weekly_report_with_ai_advice(lang: Literal["en", "zh-TW"] = Query(default="zh-TW")) -> dict:
    context, markdown = _build_weekly_payload(lang=lang)
    advice = generate_ai_advice(context, markdown, lang=lang)
    service = get_signal_service()
    signals = service.latest_signals()
    summary = summarize_signals(signals)
    return {
        "context": context.model_dump(),
        "report_markdown": markdown,
        "ai_advice": advice,
        "signals_summary": summary,
    }


@router.get("/weekly/ai")
def ai_advice_only(lang: Literal["en", "zh-TW"] = Query(default="zh-TW")) -> dict:
    """Generate rules-based market analysis."""
    context, markdown = _build_weekly_payload(lang=lang)
    advice = generate_ai_advice(context, markdown, lang=lang)
    return advice


@router.get("/weekly/fed-chair")
def fed_chair_analysis(lang: Literal["en", "zh-TW"] = Query(default="zh-TW")) -> dict:
    """Fed Chair (Powell-style) sub-agent: FOMC dual-mandate policy analysis."""
    context, markdown = _build_weekly_payload(lang=lang)
    analysis = generate_fed_chair_analysis(context, markdown, lang=lang)
    return {
        "context": context.model_dump(),
        "fed_chair_analysis": analysis,
    }
