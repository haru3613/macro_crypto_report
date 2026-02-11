"""CME FedWatch probabilities."""

from datetime import date


def fetch_fedwatch_probabilities() -> dict:
    return {
        "as_of": date(2026, 2, 9).isoformat(),
        "probabilities": {
            "cut": 0.25,
            "hold": 0.55,
            "hike": 0.20,
        },
        "source": "CME FedWatch (placeholder)",
        "is_placeholder": True,
        "note": "No free API available. Replace with live FedWatch API when accessible.",
    }
