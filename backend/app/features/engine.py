from dataclasses import dataclass
from decimal import localcontext
from ..market_data.providers.base import CandleData
from ..market_data.normalization import identity, utc
from ..market_data.quality import validate_candle
from ..cataloger.direction import direction
from .registry import create_indicator, feature_keys
from .serialization import CALC_CONTEXT
from .candle import candle_features
from .continuity import continuity


@dataclass(frozen=True)
class FeatureCandle(CandleData):
    candle_id: int = 0


def compute(candles, specs, include_candle_features=True):
    """Pure streaming causal engine. Caller must supply full snapshot prefix in time order."""
    all_keys = [key for spec in specs for key in feature_keys(spec)]
    if len(set(all_keys)) != len(all_keys):
        raise ValueError('Duplicate feature keys')
    with localcontext(CALC_CONTEXT):
        states = [(spec, create_indicator(spec)) for spec in specs]
    previous, expected, run = None, None, 0
    for candle in candles:
        with localcontext(CALC_CONTEXT):
            if validate_candle(candle): raise ValueError('Feature Engine requires valid raw candles')
            current_identity = identity(candle)
            if expected is None: expected = current_identity
            if current_identity != expected: raise ValueError('Mixed datasets are not allowed')
            timestamp = utc(candle.open_time)
            if previous is not None and timestamp <= utc(previous.open_time):
                raise ValueError('Candles must be strictly chronological')
            gap, seconds, run = continuity(candle, previous, run)
            features = candle_features(candle, previous) if include_candle_features else {}
            for spec, state in states:
                value = state.update(candle)
                features.update(zip(feature_keys(spec), value if spec.type == 'BOLLINGER' else (value,)))
            row = dict(candle_id=candle.candle_id, open_time=timestamp, close_time=utc(candle.close_time),
                       open=candle.open, high=candle.high, low=candle.low, close=candle.close,
                       direction=direction(candle), gap_before=gap, gap_seconds=seconds,
                       contiguous_run_length=run, features=features)
            previous = candle
        # Never leak the calculation context into a generator consumer.
        yield row

