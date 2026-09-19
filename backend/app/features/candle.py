from decimal import Decimal


def candle_features(candle, previous):
    body = abs(candle.close - candle.open)
    span = candle.high - candle.low
    upper = candle.high - max(candle.open, candle.close)
    lower = min(candle.open, candle.close) - candle.low
    return dict(body_size=body, candle_range=span, upper_wick=upper, lower_wick=lower,
                body_to_range_ratio=body / span if span else None,
                upper_wick_to_range_ratio=upper / span if span else None,
                lower_wick_to_range_ratio=lower / span if span else None,
                close_position=(candle.close - candle.low) / span if span else None,
                close_return_percent=(candle.close / previous.close - Decimal(1)) * 100 if previous else None)

