"""Hand-designed monotonic fixture: close=1..200, open=close, high=close+1, low=max(.5,close-1)."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.features.engine import FeatureCandle

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
META = dict(source='FEATURE_FIXTURE', broker='DEMO', symbol='EURUSD', market_type='REGULAR', timeframe='1m')


def series(values=None, size=200):
    closes = list(values) if values is not None else list(range(1, size + 1))
    return [FeatureCandle(**META, candle_id=i + 1, open_time=BASE + timedelta(minutes=i),
                          close_time=BASE + timedelta(minutes=i + 1), open=Decimal(str(value)),
                          high=Decimal(str(value)) + 1, low=max(Decimal('.5'), Decimal(str(value)) - 1),
                          close=Decimal(str(value))) for i, value in enumerate(closes)]

