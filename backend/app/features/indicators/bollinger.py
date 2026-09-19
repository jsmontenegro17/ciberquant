from .sma import SMA


class Bollinger:
    def __init__(self, period, multiplier):
        self.sma, self.multiplier = SMA(period), multiplier

    def update(self, candle):
        middle = self.sma.update(candle)
        if middle is None: return (None,) * 5
        variance = sum((value - middle) ** 2 for value in self.sma.values) / self.sma.period
        stddev = variance.sqrt()
        upper, lower = middle + self.multiplier * stddev, middle - self.multiplier * stddev
        return middle, upper, lower, stddev, (upper - lower) / middle if middle != 0 else None

