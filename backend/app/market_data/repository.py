import hashlib
import json
from sqlalchemy import select, func, text
from ..models import Candle
from .normalization import Dataset, stored_utc
from .providers.base import CandleData


def dataset_conditions(dataset):
    return [getattr(Candle, key) == value for key, value in dataset.model_dump().items()]


def lock_dataset(session, dataset):
    # Serialize competing ingestion writers even when the dataset has no rows yet.
    if session.bind.dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(json.dumps(dataset.model_dump(), sort_keys=True).encode()).digest()[:8], "big", signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


def existing_for(session, dataset, candles):
    found = {}
    for offset in range(0, len(candles), 500):
        times = [c.open_time for c in candles[offset : offset + 500]]
        query = select(Candle).where(*dataset_conditions(dataset), Candle.open_time.in_(times))
        for c in session.scalars(query):
            found[stored_utc(c.open_time)] = c
    return found


def candle_data(c):
    return CandleData(
        **{k: getattr(c, k) for k in Dataset.model_fields},
        open_time=stored_utc(c.open_time),
        close_time=stored_utc(c.close_time),
        **{k: getattr(c, k) for k in ("open", "high", "low", "close", "tick_volume", "spread")},
    )


def candle_query(dataset, start, end):
    return select(Candle).where(*dataset_conditions(dataset), Candle.open_time >= start, Candle.open_time < end).order_by(Candle.open_time)


def coverage(session, dataset=None, offset=0, limit=100):
    columns = [getattr(Candle, k) for k in Dataset.model_fields]
    query = select(
        *columns,
        func.count(Candle.id).label("candle_count"),
        func.min(Candle.open_time).label("first_candle"),
        func.max(Candle.open_time).label("last_candle"),
    )
    if dataset:
        query = query.where(*dataset_conditions(dataset))
    query = query.group_by(*columns).order_by(*columns).offset(offset).limit(limit)
    return [
        dict(row._mapping) | {"first_candle": stored_utc(row.first_candle), "last_candle": stored_utc(row.last_candle)}
        for row in session.execute(query)
    ]
