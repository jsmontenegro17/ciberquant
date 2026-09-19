from dataclasses import replace
from decimal import Decimal, localcontext, getcontext, ROUND_DOWN
from datetime import timedelta
import pytest
from pydantic import ValidationError
from app.features.engine import compute
from app.features.schemas import IndicatorSpec
from app.features.registry import STANDARD, feature_keys, definitions
from app.features.serialization import serialize, CALC_CONTEXT
from app.features.indicators.atr import true_range
from feature_fixture import series


def spec(kind, n, **kw): return IndicatorSpec(type=kind, period=n, **kw)
def run(candles, specs, **kw): return list(compute(candles, specs, **kw))
def values(rows, key): return [r['features'][key] for r in rows]


def test_sma_ema_manual_seed_alpha_and_recursion():
    rows = run(series([1, 2, 3, 6, 7]), [spec('SMA', 3), spec('EMA', 3)])
    assert serialize(values(rows, 'sma_3')) == [None, None, '2', '3.666666666666666667', '5.333333333333333333']
    assert values(rows, 'ema_3') == [None, None, Decimal(2), Decimal(4), Decimal('5.5')]


def test_ema20_exact_fixture():
    rows = run(series(size=100), [spec('EMA', 20)])
    assert values(rows, 'ema_20')[:19] == [None] * 19
    assert rows[19]['features']['ema_20'] == Decimal('10.5')
    # Linear series recurrence with alpha2/21 keeps a lag9.5: last EMA=100-9.5.
    assert serialize(rows[99]['features']['ema_20']) == '90.5'


def test_wilder_rsi_manual_smoothing():
    rows = run(series([10, 12, 11, 13, 12, 15]), [spec('RSI', 3)])
    # Seed gains4/3, losses1/3 => RSI80. Next gains8/9, losses5/9 =>800/13.
    assert serialize(values(rows, 'rsi_3')) == [None, None, None, '80', '61.538461538461538462', '81.132075471698113208']


@pytest.mark.parametrize('closes,expected', [([1, 2, 3, 4, 5], '100'), ([5, 4, 3, 2, 1], '0'), ([3] * 5, '50')])
def test_rsi_extremes(closes, expected):
    vals = serialize(values(run(series(closes), [spec('RSI', 3)]), 'rsi_3'))
    assert vals[:3] == [None] * 3 and vals[3:] == [expected] * 2


def test_true_range_wilder_atr_manual_price_gap():
    candles = [
        replace(series([10])[0], open=Decimal(10), high=Decimal(12), low=Decimal(9), close=Decimal(11)),
        replace(series([10, 14])[1], open=Decimal(14), high=Decimal(15), low=Decimal(13), close=Decimal(14)),
        replace(series([10, 14, 13])[2], open=Decimal(13), high=Decimal(14), low=Decimal(12), close=Decimal(13)),
    ]
    assert [true_range(candles[0]), true_range(candles[1], candles[0].close), true_range(candles[2], candles[1].close)] == [3, 4, 2]
    assert values(run(candles, [spec('ATR', 2)]), 'atr_2') == [None, Decimal('3.5'), Decimal('2.75')]


def test_bollinger_population_stddev_width():
    rows = run(series([1, 3, 5]), [spec('BOLLINGER', 2, stddev_multiplier='2')])
    assert all(value is None for key, value in rows[0]['features'].items() if key.startswith('bb_'))
    final = rows[1]['features']
    assert [final[f'bb_{key}_2_2'] for key in ('middle', 'stddev', 'upper', 'lower', 'width')] == [2, 1, 4, 0, 2]


def test_candle_features_zero_range_and_return():
    c = replace(series([10])[0], open=Decimal(10), close=Decimal(12), high=Decimal(14), low=Decimal(8))
    features = run([c], [])[0]['features']
    assert [features[k] for k in ('body_size', 'candle_range', 'upper_wick', 'lower_wick')] == [2, 6, 2, 2]
    assert serialize(features['body_to_range_ratio']) == '0.333333333333333333'
    assert serialize(features['close_position']) == '0.666666666666666667'
    zero = replace(series([10, 12])[1], open=Decimal(12), high=Decimal(12), low=Decimal(12), close=Decimal(12))
    row = run([c, zero], [])[1]
    assert row['features']['close_return_percent'] == 0
    assert all(row['features'][key] is None for key in ('body_to_range_ratio', 'upper_wick_to_range_ratio', 'lower_wick_to_range_ratio', 'close_position'))


def test_gap_metadata_does_not_reset_indicator_state():
    normal = series([10, 11, 12, 13, 14])
    gap = normal[:3] + [replace(c, open_time=c.open_time + timedelta(minutes=7), close_time=c.close_time + timedelta(minutes=7)) for c in normal[3:]]
    expected, actual = run(normal, STANDARD), run(gap, STANDARD)
    assert [r['features'] for r in actual] == [r['features'] for r in expected]
    assert [r['contiguous_run_length'] for r in actual] == [1, 2, 3, 1, 2]
    assert [r['gap_seconds'] for r in actual] == [0, 0, 0, 420, 0]
    assert [r['gap_before'] for r in actual] == [False, False, False, True, False]
    # Use short warmed-up recursive indicators across the same gap.
    specs = [spec(kind, 2) for kind in ('EMA', 'RSI', 'ATR')]
    assert [r['features'] for r in run(normal, specs)] == [r['features'] for r in run(gap, specs)]


def test_prefix_invariance_and_future_mutation():
    candles = series(size=200)
    prefix = run(candles[:100], STANDARD)
    assert prefix == run(candles, STANDARD)[:100]
    mutated = candles[:100] + [replace(c, open=c.open * 2, high=c.high * 2, low=c.low * 2, close=c.close * 2) for c in candles[100:]]
    assert prefix == run(mutated, STANDARD)[:100]


@pytest.mark.parametrize('field,value', [('source', 'OTHER'), ('broker', 'OTHER'), ('symbol', 'GBPUSD'), ('market_type', 'OTC'), ('timeframe', '5m')])
def test_mixed_dataset_rejected(field, value):
    candles = series(size=3)
    with pytest.raises(ValueError, match='Mixed'):
        run([candles[0], replace(candles[1], **{field: value})], STANDARD)


def test_context_independence_no_leak_and_serialization():
    candles = series([10, 12, 11, 13, 12, 15])
    expected = serialize(run(candles, STANDARD))
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 8, ROUND_DOWN
        generator = compute(candles, STANDARD)
        next(generator)
        assert getcontext().prec == 8 and getcontext().rounding == ROUND_DOWN
        assert serialize(run(candles, STANDARD)) == expected
    assert serialize(Decimal('1.2345678901234567885')) == '1.234567890123456788'
    assert serialize(Decimal('1.2345678901234567895')) == '1.23456789012345679'


@pytest.mark.parametrize('kwargs', [
    {'type': 'EMA', 'period': 1}, {'type': 'EMA', 'period': 501}, {'type': 'EMA', 'period': 2.5},
    {'type': 'MACD', 'period': 20}, {'type': 'EMA', 'period': 20, 'stddev_multiplier': '2'},
    *[{'type': 'BOLLINGER', 'period': 20, 'stddev_multiplier': x} for x in ('0', '-1', '11', 'NaN', 'Infinity', '2.1234567', 2.5)]
])
def test_invalid_specs(kwargs):
    with pytest.raises(ValidationError): IndicatorSpec(**kwargs)


def test_registry_keys_warmup_and_no_candle_features():
    assert feature_keys(spec('BOLLINGER', 20, stddev_multiplier='2.500')) == ['bb_middle_20_2p5', 'bb_upper_20_2p5', 'bb_lower_20_2p5', 'bb_stddev_20_2p5', 'bb_width_20_2p5']
    entries = definitions(12)['supported_indicators']
    assert next(e for e in entries if e['type'] == 'RSI')['warmup_requirement'] == 15
    assert next(e for e in entries if e['type'] == 'EMA')['warmup_requirement'] == 20
    assert run(series(size=1), [], include_candle_features=False)[0]['features'] == {}
    with pytest.raises(ValueError): run(series(size=3), [spec('EMA', 2)] * 2)
