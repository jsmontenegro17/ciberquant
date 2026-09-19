from . import FEATURE_ENGINE_VERSION
from .schemas import IndicatorSpec
from .indicators.sma import SMA
from .indicators.ema import EMA
from .indicators.rsi import RSI
from .indicators.atr import ATR
from .indicators.bollinger import Bollinger

REGISTRY = {'SMA': SMA, 'EMA': EMA, 'RSI': RSI, 'ATR': ATR, 'BOLLINGER': Bollinger}
DEFAULT_PERIODS = {'SMA': 20, 'EMA': 20, 'RSI': 14, 'ATR': 14, 'BOLLINGER': 20}
CANDLE_KEYS = ['body_size', 'candle_range', 'upper_wick', 'lower_wick', 'body_to_range_ratio',
               'upper_wick_to_range_ratio', 'lower_wick_to_range_ratio', 'close_position', 'close_return_percent']


def feature_keys(spec):
    if spec.type == 'BOLLINGER':
        multiplier = format(spec.stddev_multiplier, 'f')
        if '.' in multiplier: multiplier = multiplier.rstrip('0').rstrip('.')
        suffix = f'{spec.period}_{multiplier.replace(".", "p")}'
        return [f'bb_{key}_{suffix}' for key in ('middle', 'upper', 'lower', 'stddev', 'width')]
    return [f'{spec.type.lower()}_{spec.period}']


def describe(spec):
    return {'type': spec.type, 'parameters': spec.model_dump(exclude={'type'}, exclude_none=True),
            'constraints': {'period': {'min': 2, 'max': 500}, **({'stddev_multiplier': {'exclusive_min': '0', 'max': '10', 'decimal_places': 6}} if spec.type == 'BOLLINGER' else {})},
            'generated_feature_keys': feature_keys(spec), 'warmup_requirement': spec.period + (1 if spec.type == 'RSI' else 0),
            'calculation_version': FEATURE_ENGINE_VERSION}


def create_indicator(spec):
    factory = REGISTRY[spec.type]
    return factory(spec.period, spec.stddev_multiplier) if spec.type == 'BOLLINGER' else factory(spec.period)


STANDARD = [IndicatorSpec(type='EMA', period=n) for n in (9, 20, 50)] + [
    IndicatorSpec(type='RSI', period=14), IndicatorSpec(type='ATR', period=14), IndicatorSpec(type='BOLLINGER', period=20)]


def definitions(max_specs):
    supported = []
    for name, period in DEFAULT_PERIODS.items():
        spec = IndicatorSpec(type=name, period=period)
        supported.append({**describe(spec), 'key_templates': [k.replace(str(period), '{period}', 1).replace('_2', '_{multiplier}') if name == 'BOLLINGER' else k.replace(str(period), '{period}', 1) for k in feature_keys(spec)],
                          'warmup_definition': 'period + 1 candles' if name == 'RSI' else 'period candles'})
    return {'calculation_version': FEATURE_ENGINE_VERSION, 'supported_indicators': supported,
            'candle_feature_keys': CANDLE_KEYS, 'defaults': {'STANDARD': [s.model_dump(exclude_none=True) for s in STANDARD]},
            'max_indicator_specs': max_specs}

