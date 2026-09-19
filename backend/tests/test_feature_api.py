from dataclasses import asdict, replace
from datetime import timedelta
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from app.models import Candle, User
from app.config import settings
from app.features.schemas import ComputeRequest
from app.features.repository import calculate_snapshot
from app.features.serialization import serialize
from app.features.registry import STANDARD
from feature_fixture import series, META, BASE
from test_req003 import harness  # noqa: F401
from test_market_data_migration import migrated_database  # noqa: F401


def seed(factory, candles=None):
    with factory() as session:
        for candle in candles if candles is not None else series():
            values = asdict(candle)
            values.pop('candle_id')
            session.add(Candle(**values))
        session.commit()


def body(start=0, end=200, **changes):
    return dict(dataset=META, start=(BASE + timedelta(minutes=start)).isoformat(),
                end=(BASE + timedelta(minutes=end)).isoformat(),
                indicators=[s.model_dump(mode='json', exclude_none=True) for s in STANDARD], **changes)


def test_user_definitions_range_independence_and_no_writes(harness):
    client, factory, uid = harness
    seed(factory)
    with factory() as s:
        s.get(User, uid).role = 'USER'
        s.commit()
    definitions = client.get('/api/v1/features/definitions')
    assert definitions.status_code == 200
    assert len(definitions.json()['defaults']['STANDARD']) == 6
    first = client.post('/api/v1/features/compute', json=body(start=50))
    assert first.status_code == 200, first.text
    a = first.json()
    b = client.post('/api/v1/features/compute', json=body(start=80, as_of_candle_id=a['metadata']['as_of_candle_id'])).json()
    assert a['rows'][30:] == b['rows']
    assert b['metadata']['candles_processed'] == 200
    assert b['metadata']['rows_returned'] == 120
    assert b['metadata']['calculation_anchor'] == BASE.isoformat()
    assert b['rows'][19]['features']['ema_20'] == '90.5'
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Candle)) == 200
        assert s.scalar(select(Candle.close).order_by(Candle.id)) == 1


def test_snapshot_excludes_late_backfill_and_future(migrated_database):
    factory = sessionmaker(bind=migrated_database)
    seed(factory, series(size=100))
    with factory() as s:
        before = serialize(calculate_snapshot(s, ComputeRequest(**body(end=100))))
    original = series(size=1)[0]
    seed(factory, [replace(original, open_time=BASE-timedelta(minutes=1), close_time=BASE)])
    seed(factory, series()[100:])
    with factory() as s:
        fixed = serialize(calculate_snapshot(s, ComputeRequest(**body(end=100, as_of_candle_id=before['metadata']['as_of_candle_id']))))
        fresh = serialize(calculate_snapshot(s, ComputeRequest(**body(end=100))))
    assert fixed == before
    assert fresh['metadata']['candles_processed'] == 101
    assert fresh['metadata']['calculation_anchor'] != before['metadata']['calculation_anchor']


@pytest.mark.parametrize('field,value', [('source','OTHER'), ('broker','OTHER'), ('symbol','GBPUSD'), ('market_type','OTC'), ('timeframe','5m')])
def test_repository_dataset_isolation(harness, field, value):
    client, factory, _ = harness
    seed(factory, series(size=2))
    other = replace(series(size=1)[0], **{field:value})
    if field == 'timeframe':
        other = replace(other, close_time=other.open_time + timedelta(minutes=5))
    seed(factory, [other])
    response = client.post('/api/v1/features/compute', json=body()).json()
    assert response['metadata']['candles_processed'] == 2
    assert response['metadata']['as_of_candle_id'] == 2
    assert len(response['rows']) == 2


@pytest.mark.parametrize('setting', ['feature_api_max_return_rows', 'feature_engine_max_source_candles'])
def test_caps_reject_without_truncation(harness, monkeypatch, setting):
    client, factory, _ = harness
    seed(factory, series(size=3))
    monkeypatch.setattr(settings, setting, 2)
    response = client.post('/api/v1/features/compute', json=body())
    assert response.status_code == 422 and 'exceeds' in response.text


def test_empty_warmup_invalid_snapshot_and_dates(harness):
    client, factory, _ = harness
    empty = client.post('/api/v1/features/compute', json=body()).json()
    assert empty['rows'] == [] and empty['metadata']['calculation_anchor'] is None
    assert empty['metadata']['as_of_candle_id'] == 0
    seed(factory, series(size=1))
    response = client.post('/api/v1/features/compute', json=body(include_candle_features=False)).json()
    assert all(v is None for v in response['rows'][0]['features'].values())
    assert 'body_size' not in response['feature_keys']
    for changes in [dict(as_of_candle_id=2), dict(start='2026-01-01T00:00:00'), dict(end=0), dict(indicators=[{'type':'EMA','period':1}])]:
        payload = {**body(), **changes}
        assert client.post('/api/v1/features/compute', json=payload).status_code == 422
