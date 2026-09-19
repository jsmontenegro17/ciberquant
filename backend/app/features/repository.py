from dataclasses import asdict
from sqlalchemy import select, func
from ..models import Candle
from ..market_data.repository import dataset_conditions, candle_data
from ..market_data.normalization import stored_utc
from ..config import settings
from .engine import FeatureCandle, compute
from .registry import feature_keys, CANDLE_KEYS, describe
from . import FEATURE_ENGINE_VERSION


def calculate_snapshot(session, request):
    conditions = dataset_conditions(request.dataset)
    maximum = session.scalar(select(func.max(Candle.id)).where(*conditions)) or 0
    ceiling = maximum if request.as_of_candle_id is None else request.as_of_candle_id
    if ceiling > maximum:
        raise ValueError('as_of_candle_id exceeds dataset maximum; use a returned snapshot ID')
    snapshot = [*conditions, Candle.id <= ceiling]
    anchor = session.scalar(select(func.min(Candle.open_time)).where(*snapshot))
    source = [*snapshot, Candle.open_time < request.end]
    source_count = session.scalar(select(func.count()).select_from(Candle).where(*source))
    returned_count = session.scalar(select(func.count()).select_from(Candle).where(*source, Candle.open_time >= request.start))
    if source_count > settings.feature_engine_max_source_candles:
        raise ValueError(f'Exact origin calculation exceeds {settings.feature_engine_max_source_candles} source candles; choose an earlier end or smaller snapshot. No approximate seed is used.')
    if returned_count > settings.feature_api_max_return_rows:
        raise ValueError(f'Response exceeds {settings.feature_api_max_return_rows} rows; narrow the output date range')
    statement = select(Candle).where(*source).order_by(Candle.open_time).limit(settings.feature_engine_max_source_candles + 1)
    candles = (FeatureCandle(**asdict(candle_data(c)), candle_id=c.id) for c in session.scalars(statement.execution_options(yield_per=1000)))
    rows, processed = [], 0
    for row in compute(candles, request.indicators, request.include_candle_features):
        processed += 1
        if processed > settings.feature_engine_max_source_candles:
            raise ValueError('Source cap exceeded; calculation rejected without truncation')
        if row['open_time'] >= request.start:
            rows.append(row)
            if len(rows) > settings.feature_api_max_return_rows:
                raise ValueError('Return cap exceeded; calculation rejected without truncation')
    return {'metadata': {'dataset': request.dataset.model_dump(), 'as_of_candle_id': ceiling,
                         'calculation_version': FEATURE_ENGINE_VERSION,
                         'calculation_anchor': stored_utc(anchor) if anchor else None,
                         'requested_start': request.start, 'requested_end': request.end,
                         'candles_processed': processed, 'rows_returned': len(rows),
                         'include_candle_features': request.include_candle_features,
                         'indicators': [describe(spec) for spec in request.indicators]},
            'feature_keys': (CANDLE_KEYS if request.include_candle_features else []) + [key for spec in request.indicators for key in feature_keys(spec)],
            'rows': rows}

