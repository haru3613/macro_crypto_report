"""CME futures gap detection."""


def detect_cme_gap(ohlc: list[dict]) -> dict:
    if len(ohlc) < 2:
        return {"gap": 0, "status": "insufficient_data"}

    prev_close = ohlc[-2]["close"]
    current_open = ohlc[-1]["open"]
    gap = current_open - prev_close
    status = "gap_up" if gap > 0 else "gap_down" if gap < 0 else "flat"
    return {
        "gap": gap,
        "status": status,
        "prev_close": prev_close,
        "current_open": current_open,
    }
