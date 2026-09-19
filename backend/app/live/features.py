"""Persistent consumer of the unmodified frozen streaming Feature Engine."""

from collections import deque
from ..features.engine import compute


class IncrementalFeatures:
    def __init__(self, specs):
        self.pending = deque()
        self.rows = deque(maxlen=51)
        self.stream = compute(self._source(), specs)

    def _source(self):
        while True:
            yield self.pending.popleft()

    def update(self, closed_candle):
        self.pending.append(closed_candle)
        row = next(self.stream)
        self.rows.append(row)
        return row
