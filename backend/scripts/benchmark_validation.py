"""100k deterministic candles; pure computation, no SLA/SQL/JSON claim."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from time import perf_counter
import platform
import os
from app.features.engine import FeatureCandle, compute
from app.features.registry import STANDARD
from app.strategies.schemas import VersionCreate
from app.validation.schemas import ValidationCreate
from app.validation.protocol import split, bootstrap
from app.backtesting.engine import simulate_rows
from app.strategies.dsl import digest


def main():
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    meta = dict(source="BENCHMARK", broker="SYNTHETIC", symbol="FIXTURE", market_type="REGULAR", timeframe="1m")
    candles = [
        FeatureCandle(
            **meta,
            candle_id=i + 1,
            open_time=base + timedelta(minutes=i),
            close_time=base + timedelta(minutes=i + 1),
            open=Decimal(100),
            high=Decimal(102),
            low=Decimal(99),
            close=Decimal(101),
            tick_volume=None,
            spread=None,
        )
        for i in range(100000)
    ]
    d = VersionCreate(
        trade_direction="CALL",
        indicator_specs=STANDARD,
        condition_tree={
            "left": {"type": "FIELD", "field": "close", "bars_ago": 0},
            "operator": "GT",
            "right": {"type": "NUMBER", "value": "0"},
        },
    )
    req = ValidationCreate(
        strategy_version_id=1, dataset=meta, overall_start=base, overall_end=candles[-1].close_time, payout_percent="83.5", expiry_bars=1
    )
    parts = split(candles, req.overall_start, req.overall_end)
    mark = perf_counter()
    rows = list(compute(candles[:80000], d.indicator_specs))
    timings = {"development_features": perf_counter() - mark}
    for kind, fold, start, end in parts:
        if kind == "TEST":
            continue
        mark = perf_counter()
        simulate_rows(rows, d, req.child(start, end, 100000), lambda: timedelta(minutes=1), max_trades=100000)
        timings[f"{kind}_{fold}"] = perf_counter() - mark
    mark = perf_counter()
    rows = list(compute(candles, d.indicator_specs))
    timings["reveal_features"] = perf_counter() - mark
    _, _, start, end = parts[2]
    mark = perf_counter()
    result = simulate_rows(rows, d, req.child(start, end, 100000), lambda: timedelta(minutes=1), max_trades=100000)
    timings["test_execution"] = perf_counter() - mark
    mark = perf_counter()
    bootstrap(result["trades"], digest(req.model_dump(mode="json")))
    timings["test_bootstrap"] = perf_counter() - mark
    print(
        dict(
            platform=platform.platform(),
            cpu=platform.processor(),
            logical_cpus=os.cpu_count(),
            python=platform.python_version(),
            candles=100000,
            explicit_benchmark_trade_cap=100000,
            timings=timings,
        )
    )


if __name__ == "__main__":
    main()
