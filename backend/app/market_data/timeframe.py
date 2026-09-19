from datetime import timedelta

TIMEFRAMES = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}
ALIASES = {"m1": "1m", "m5": "5m", "m15": "15m", "m30": "30m", "h1": "1h"}


def normalize_timeframe(value: str) -> str:
    value = value.strip().lower()
    value = ALIASES.get(value, value)
    if value not in TIMEFRAMES:
        raise ValueError("Unsupported timeframe; use 1m, 5m, 15m, 30m or 1h")
    return value


def duration(value: str) -> timedelta:
    return timedelta(seconds=TIMEFRAMES[normalize_timeframe(value)])
