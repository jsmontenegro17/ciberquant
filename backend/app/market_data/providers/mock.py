from .base import MarketDataProvider


class MockMarketDataProvider(MarketDataProvider):
    def __init__(self, candles=None):
        self.candles = candles or []

    def get_historical_candles(self, **kwargs):
        return list(self.candles)

    def get_latest_candles(self, **kwargs):
        return list(self.candles[-1:])

    def stream_candles(self, **kwargs):
        yield from self.candles

    def get_assets(self):
        return sorted({c.symbol for c in self.candles})
