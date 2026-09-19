from decimal import Decimal
from .sma import SMA


class RSI:
    def __init__(self, period):
        self.period, self.previous = period, None
        self.gains, self.losses = SMA(period), SMA(period)
        self.avg_gain = self.avg_loss = None

    def update(self, candle):
        if self.previous is None:
            self.previous = candle.close
            return None
        delta = candle.close - self.previous
        self.previous = candle.close
        gain, loss = max(delta, Decimal(0)), max(-delta, Decimal(0))
        if self.avg_gain is None:
            self.avg_gain, self.avg_loss = self.gains.update_value(gain), self.losses.update_value(loss)
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period
        if self.avg_gain is None: return None
        if self.avg_loss == 0: return Decimal(100) if self.avg_gain > 0 else Decimal(50)
        if self.avg_gain == 0: return Decimal(0)
        return 100 - 100 / (1 + self.avg_gain / self.avg_loss)

