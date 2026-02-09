"""API routes for weekly report generation."""

from fastapi import APIRouter
from fastapi import Query

from app.config import get_settings
from data.fetch_all import fetch_all_sources
from indicators.compute import compute_report_context
from report.ai_advice import generate_ai_advice
from report.render import render_report
from services.signal_service import get_signal_service

router = APIRouter()


def _build_weekly_payload(lang: str) -> tuple:
    raw_data = fetch_all_sources()
    context = compute_report_context(raw_data)
    markdown = render_report(context, lang=lang)
    return context, markdown


@router.get("/weekly")
def weekly_report(lang: str = Query(default="zh-TW")) -> dict:
    context, markdown = _build_weekly_payload(lang=lang)
    return {
        "context": context.model_dump(),
        "report_markdown": markdown,
    }


@router.get("/weekly/advice")
def weekly_report_with_ai_advice(lang: str = Query(default="zh-TW")) -> dict:
    context, markdown = _build_weekly_payload(lang=lang)
    advice = generate_ai_advice(context, markdown, lang=lang, settings=get_settings())
    service = get_signal_service()
    signals = service.latest_signals()
    summary = summarize_signals(signals)
    return {
        "context": context.model_dump(),
        "report_markdown": markdown,
        "ai_advice": advice,
        "signals_summary": summary,
    }


def summarize_signals(signals: list[dict]) -> dict:
    summary: dict[str, dict[str, int]] = {
        "15m": {"buy": 0, "sell": 0, "hold": 0},
        "1d": {"accumulate": 0, "reduce": 0, "hold": 0},
    }
    for signal in signals:
        timeframe = signal["timeframe"]
        action = signal["action"]
        if timeframe in summary and action in summary[timeframe]:
            summary[timeframe][action] += 1
    return summary
