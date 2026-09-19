"""Pure-engine throughput observation, not an SLA. Run from backend: python scripts/benchmark_features.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
import platform
from time import perf_counter
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.features.engine import FeatureCandle, compute
from app.features.registry import STANDARD
from app.features import FEATURE_ENGINE_VERSION


def candles(count):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        close = Decimal(100) + Decimal(i % 1000) / 100
        yield FeatureCandle(source='BENCHMARK', broker='SYNTHETIC', symbol='TEST', market_type='REGULAR', timeframe='1m',
                            candle_id=i+1, open_time=base+timedelta(minutes=i), close_time=base+timedelta(minutes=i+1),
                            open=close, high=close+1, low=close-1, close=close)


if __name__ == '__main__':
    start = perf_counter()
    count = sum(1 for _ in compute(candles(100_000), STANDARD))
    print(dict(engine=FEATURE_ENGINE_VERSION, platform=platform.platform(), processor=platform.processor(),
               logical_cpus=os.cpu_count(), python=platform.python_version(), candles=count,
               indicators=[s.model_dump(mode='json', exclude_none=True) for s in STANDARD],
               seconds=round(perf_counter()-start, 3), context='single process, Decimal precision50, synthetic generation included; no SQL/serialization; not an SLA'))
