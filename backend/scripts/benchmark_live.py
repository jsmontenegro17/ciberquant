"""Synthetic multi-dataset incremental pipeline; no DB/network throughput or SLA claim."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from time import perf_counter
import json
import platform
from app.features.engine import FeatureCandle
from app.features.registry import STANDARD
from app.live.features import IncrementalFeatures
from app.strategies.schemas import VersionCreate
from app.strategies.dsl import evaluate, Truth


def main():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    states = [IncrementalFeatures(STANDARD) for _ in range(3)]
    definitions = [
        VersionCreate(
            trade_direction="CALL",
            indicator_specs=STANDARD,
            condition_tree={
                "left": {"type": "FIELD", "field": "close", "bars_ago": 0},
                "operator": "GT",
                "right": {"type": "NUMBER", "value": str(100 + i)},
            },
        )
        for i in range(4)
    ]
    updates = evals = events = matches = 0
    feature_seconds = 0
    started = perf_counter()
    for i in range(10000):
        price = Decimal(100) + Decimal(i % 101) / 10
        for index, state in enumerate(states):
            candle = FeatureCandle(
                source="BENCHMARK",
                broker="SYNTHETIC",
                symbol=f"ASSET{index}",
                market_type="REGULAR",
                timeframe="1m",
                open_time=base + timedelta(minutes=i),
                close_time=base + timedelta(minutes=i + 1),
                open=price,
                high=price + 2,
                low=price - 2,
                close=price + 1,
            )
            tick = perf_counter()
            row = state.update(candle)
            feature_seconds += perf_counter() - tick
            updates += 1
            for definition in definitions:
                truth, _ = evaluate(definition.condition_tree, state.rows, row["close_time"])
                evals += 1
                events += 1
                matches += truth == Truth.TRUE
    elapsed = perf_counter() - started
    print(
        json.dumps(
            dict(
                python=platform.python_version(),
                platform=platform.system(),
                datasets=3,
                strategies_per_dataset=4,
                candles_per_dataset=10000,
                elapsed_seconds=elapsed,
                events_per_second=events / elapsed,
                strategy_evaluations_per_second=evals / elapsed,
                mean_feature_update_microseconds=feature_seconds * 1e6 / updates,
                evaluations=evals,
                matches=matches,
                scope="In-memory event decisions, excludes SQL/network/JSON; not an SLA",
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
