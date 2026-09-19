from collections import deque
from decimal import Decimal


class SMA:
    def __init__(self, period):
        self.period, self.values, self.total = period, deque(), Decimal(0)

    def update_value(self, value):
        self.values.append(value)
        self.total += value
        if len(self.values) > self.period:
            self.total -= self.values.popleft()
        return self.total / self.period if len(self.values) == self.period else None

    def update(self, candle): return self.update_value(candle.close)

