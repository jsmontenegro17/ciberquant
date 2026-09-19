from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from datetime import datetime
from ..market_data.normalization import utc

CALC_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal('0.000000000000000001')


def serialize(value):
    if isinstance(value, Decimal):
        with localcontext(CALC_CONTEXT):
            rounded = value.quantize(QUANTUM)
        if rounded == 0:
            return '0'
        return format(rounded, 'f').rstrip('0').rstrip('.') if '.' in format(rounded, 'f') else format(rounded, 'f')
    if isinstance(value, datetime):
        return utc(value).isoformat()
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    return value

