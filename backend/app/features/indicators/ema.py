from decimal import Decimal
from .sma import SMA


class EMA:
    def __init__(self, period):
        self.seed = SMA(period)
        self.alpha = Decimal(2) / (period + 1)
        self.value = None

    def update(self, candle):
        if self.value is None:
            self.value = self.seed.update(candle)
        else:
            self.value = self.alpha * candle.close + (1 - self.alpha) * self.value
        return self.value

