from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CandleData:
    source: str
    symbol: str
    market_type: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    broker: str = "UNSPECIFIED"
    tick_volume: Decimal | None = None
    spread: Decimal | None = None


class MarketDataProvider:
    def get_historical_candles(self, **kwargs):
        raise NotImplementedError

    def get_latest_candles(self, **kwargs):
        raise NotImplementedError

    def stream_candles(self, **kwargs):
        raise NotImplementedError

    def get_assets(self):
        raise NotImplementedError
