from .sma import SMA


def true_range(candle, previous_close=None):
    return candle.high - candle.low if previous_close is None else max(
        candle.high - candle.low, abs(candle.high - previous_close), abs(candle.low - previous_close))


class ATR:
    def __init__(self, period):
        self.period, self.previous, self.value = period, None, None
        self.seed = SMA(period)

    def update(self, candle):
        value = true_range(candle, self.previous)
        self.previous = candle.close
        if self.value is None:
            self.value = self.seed.update_value(value)
        else:
            self.value = (self.value * (self.period - 1) + value) / self.period
        return self.value

