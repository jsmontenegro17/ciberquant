from decimal import Decimal


def summarize(pattern, observations):
    counts = observations["counts"]
    size = sum(counts.values())
    return dict(
        pattern=pattern,
        pattern_length=len(pattern),
        sample_size=size,
        next_bullish_count=counts["C"],
        next_bearish_count=counts["P"],
        next_doji_count=counts["D"],
        next_bullish_probability=Decimal(counts["C"]) / Decimal(size),
        next_bearish_probability=Decimal(counts["P"]) / Decimal(size),
        next_doji_probability=Decimal(counts["D"]) / Decimal(size),
        first_observation=observations["first"],
        last_observation=observations["last"],
        distinct_days=len(observations["days"]),
    )
