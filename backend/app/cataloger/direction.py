def direction(candle):
    """C=bullish, P=bearish, D=exact doji; never a trade recommendation."""
    return "C" if candle.close > candle.open else "P" if candle.close < candle.open else "D"
