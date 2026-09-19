from datetime import datetime,timezone,timedelta
from decimal import Decimal
from app.services.market_data import CandleData,validate_candle,validate_candles
def c(**kw):
    d=datetime.now(timezone.utc); base=dict(source='test',symbol='EURUSD',market_type='REGULAR',timeframe='1m',open_time=d,close_time=d+timedelta(minutes=1),open=Decimal('1.1'),high=Decimal('1.2'),low=Decimal('1.0'),close=Decimal('1.15')); base.update(kw); return CandleData(**base)
def test_invalid_ohlc(): assert validate_candle(c(high=Decimal('0.9')))
def test_valid(): assert validate_candle(c())==[]
def test_duplicate_and_otc_quality_errors():
    candle=c(); assert validate_candles([candle,candle])
    assert validate_candle(c(symbol='EURUSD-OTC',market_type='REGULAR'))
