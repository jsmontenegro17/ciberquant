from decimal import Decimal
from datetime import timedelta
from ..market_data.timeframe import duration


def continuity(candle, previous, run):
    if previous is None: return False, Decimal(0), 1
    delta = candle.open_time - previous.open_time
    missing = delta - duration(candle.timeframe)
    seconds = Decimal(missing.days * 86400 + missing.seconds) + Decimal(missing.microseconds) / Decimal(1000000)
    gap = missing != timedelta(0)
    return gap, seconds, 1 if gap else run + 1
