from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import csv
@dataclass(frozen=True)
class CandleData:
    source:str; symbol:str; market_type:str; timeframe:str; open_time:datetime; close_time:datetime; open:Decimal; high:Decimal; low:Decimal; close:Decimal
class MarketDataProvider:
    def get_historical_candles(self, **kwargs): raise NotImplementedError
    def get_latest_candles(self, **kwargs): raise NotImplementedError
    def stream_candles(self, **kwargs): raise NotImplementedError
    def get_assets(self): raise NotImplementedError
class MockMarketDataProvider(MarketDataProvider):
    def __init__(self, candles:list[CandleData]|None=None): self.candles=candles or []
    def get_historical_candles(self, **kwargs): return list(self.candles)
    def get_latest_candles(self, **kwargs): return list(self.candles[-1:])
    def stream_candles(self, **kwargs): yield from self.candles
    def get_assets(self): return sorted({c.symbol for c in self.candles})
class CSVMarketDataProvider(MarketDataProvider):
    def __init__(self, path): self.path=path
    def get_historical_candles(self, **kwargs):
        with open(self.path, newline='', encoding='utf-8') as f:
            return [CandleData(row['source'],row['symbol'],row['market_type'],row['timeframe'],datetime.fromisoformat(row['open_time']),datetime.fromisoformat(row['close_time']),*(Decimal(row[k]) for k in ('open','high','low','close'))) for row in csv.DictReader(f)]
    def get_latest_candles(self, **kwargs): return self.get_historical_candles()[-1:]
    def stream_candles(self, **kwargs): yield from self.get_historical_candles()
    def get_assets(self): return sorted({c.symbol for c in self.get_historical_candles()})
def validate_candle(c:CandleData):
    if c.high < c.low or c.open < c.low or c.open > c.high or c.close < c.low or c.close > c.high: return ['OHLC values outside range']
    if c.close_time <= c.open_time: return ['timestamps must be increasing']
    if '-OTC' in c.symbol and c.market_type != 'OTC': return ['OTC symbol must use OTC market_type']
    return []
def validate_candles(candles:list[CandleData]):
    errors=[]; seen=set()
    for candle in candles:
        identity=(candle.source,candle.symbol,candle.market_type,candle.timeframe,candle.open_time)
        if identity in seen: errors.append(f'duplicate candle: {identity}')
        seen.add(identity); errors.extend(validate_candle(candle))
    return errors
