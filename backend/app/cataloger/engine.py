from collections import deque
from .direction import direction
from .statistics import summarize
from ..market_data.normalization import identity, utc
from ..market_data.timeframe import duration
from ..market_data.quality import validate_candle


def analyze(candles, pattern_length=3, include_doji=True):
    """Pure O(n * L), L <= 5. Outcome belongs to each complete contiguous window."""
    if pattern_length not in (2, 3, 4, 5):
        raise ValueError("pattern_length must be 2–5")
    patterns = {}
    window = deque(maxlen=pattern_length + 1)
    previous = None
    expected_identity = None
    examined = eligible = gaps = dojis = 0
    for candle in candles:
        if validate_candle(candle):
            raise ValueError("Cataloger requires validated candles")
        if expected_identity is None:
            expected_identity = identity(candle)
        if identity(candle) != expected_identity:
            raise ValueError("Cataloger input must contain one dataset")
        timestamp = utc(candle.open_time)
        if previous is not None and timestamp <= previous:
            raise ValueError("Cataloger input must be strictly chronological")
        previous = timestamp
        examined += 1
        window.append((timestamp, direction(candle)))
        if len(window) != pattern_length + 1:
            continue
        items = list(window)
        if any(items[i + 1][0] - items[i][0] != duration(candle.timeframe) for i in range(pattern_length)):
            gaps += 1
            continue
        if not include_doji and any(code == "D" for _, code in items):
            dojis += 1
            continue
        eligible += 1
        pattern = "".join(code for _, code in items[:-1])
        outcome_time, outcome = items[-1]
        stat = patterns.setdefault(
            pattern, {"counts": {"C": 0, "P": 0, "D": 0}, "first": outcome_time, "last": outcome_time, "days": set()}
        )
        stat["counts"][outcome] += 1
        stat["last"] = outcome_time
        stat["days"].add(outcome_time.date())
    return dict(
        candles_examined=examined,
        eligible_windows=eligible,
        windows_skipped_due_to_gaps=gaps,
        windows_skipped_due_to_doji=dojis,
        patterns=[summarize(p, patterns[p]) for p in sorted(patterns)],
    )
