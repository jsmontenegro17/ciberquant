from dataclasses import asdict
from decimal import Decimal
from ..backtesting.outcome import resolve
from ..market_data.timeframe import duration


class PaperObservation:
    def __init__(self, event_id, signal_candle, direction, expiry, payout, payout_source):
        self.event_id, self.direction, self.remaining = event_id, direction, expiry
        self.step = duration(signal_candle.timeframe)
        self.expected = signal_candle.open_time + self.step
        self.previous_close = signal_candle.close_time
        self.payout, self.source = Decimal(payout), payout_source
        self.entry = None

    def update(self, candle):
        if candle.open_time != self.expected or candle.open_time < self.previous_close:
            return dict(result="GAP", expected_entry_time=self.expected, reason="Nonconsecutive observed entry/expiry")
        if self.entry is None:
            self.entry = candle
        self.remaining -= 1
        self.expected = candle.open_time + self.step
        self.previous_close = candle.close_time
        if self.remaining:
            return None
        result = asdict(resolve(self.direction, self.entry.open_time, self.entry.open, candle.close_time, candle.close, self.payout))
        return {**result, "expected_entry_time": self.entry.open_time, "payout_snapshot": self.payout, "payout_source": self.source}
