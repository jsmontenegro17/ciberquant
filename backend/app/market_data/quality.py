from decimal import Decimal, InvalidOperation
from .normalization import utc, identity
from .timeframe import duration

PRICE_FIELDS = ("open", "high", "low", "close")
VALUE_FIELDS = (*PRICE_FIELDS, "tick_volume", "spread")


def decimal_value(raw: str) -> Decimal:
    try:
        value = Decimal(raw)
        if not value.is_finite() or abs(value) >= Decimal("100000000000000"):
            raise ValueError("Number must be finite and fit Numeric(24,10)")
        if value != value.quantize(Decimal("0.0000000001")):
            raise ValueError("Maximum 10 decimal places; rounding is not allowed")
        return value
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid decimal") from exc


def validate_candle(c):
    errors = []
    for field in VALUE_FIELDS:
        value = getattr(c, field)
        if value is None and field not in PRICE_FIELDS:
            continue
        try:
            value = decimal_value(str(value))
            if value < 0 or (field in PRICE_FIELDS and value == 0):
                errors.append(f"{field}: must be positive (volume/spread may be zero)")
        except ValueError as exc:
            errors.append(f"{field}: {exc}")
    if not errors and (c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.high < c.low):
        errors.append("OHLC values outside range")
    try:
        if utc(c.close_time) <= utc(c.open_time):
            errors.append("close_time must be after open_time")
        duration(c.timeframe)
    except ValueError as exc:
        errors.append(str(exc))
    if c.market_type not in ("REGULAR", "OTC"):
        errors.append("Invalid market_type")
    if "-OTC" in c.symbol.upper() and c.market_type != "OTC":
        errors.append("OTC symbol must use OTC market_type")
    return errors


def validate_candles(candles):
    errors, seen = [], set()
    previous = None
    for c in candles:
        key = (*identity(c), c.open_time)
        if key in seen:
            errors.append("Duplicate candle in file")
        seen.add(key)
        errors.extend(validate_candle(c))
        if previous is not None:
            if identity(previous) != identity(c):
                errors.append("Mixed datasets")
            elif c.open_time <= previous.open_time:
                errors.append("Candles must be strictly chronological")
        previous = c
    return errors
