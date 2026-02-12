#!/usr/bin/env python3
"""Export current report context as JSON for Claude subagent analysis.

Usage:
    python scripts/export_context.py [--lang zh-TW|en] [--output FILE]

If the API server is running, fetches from /report/weekly.
Otherwise, fetches data sources directly.

Output is written to stdout (or --output file) for piping to Claude.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _fetch_from_api(lang: str) -> dict | None:
    """Try fetching from running API server."""
    from urllib.request import urlopen
    from urllib.error import URLError

    url = f"http://localhost:8000/report/weekly?lang={lang}"
    try:
        with urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, ConnectionError, OSError):
        return None


def _fetch_direct(lang: str) -> dict:
    """Fetch data sources directly (no server needed)."""
    from data.fetch_all import fetch_all_sources
    from indicators.compute import compute_report_context
    from report.render import render_report

    raw_data = fetch_all_sources()
    context = compute_report_context(raw_data)
    markdown = render_report(context, lang=lang)
    return {
        "context": context.model_dump(),
        "report_markdown": markdown,
    }


def main():
    parser = argparse.ArgumentParser(description="Export report context for analysis")
    parser.add_argument("--lang", default="zh-TW", choices=["zh-TW", "en"])
    parser.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    # Try API first, fallback to direct fetch
    data = _fetch_from_api(args.lang)
    if data is None:
        print("API not available, fetching directly...", file=sys.stderr)
        data = _fetch_direct(args.lang)
    else:
        print("Fetched from running API server.", file=sys.stderr)

    output = json.dumps(data, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
