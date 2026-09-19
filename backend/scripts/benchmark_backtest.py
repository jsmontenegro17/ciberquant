"""100k causal pipeline observation; no production SLA or financial claim."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import platform
import os
from datetime import datetime, timezone, timedelta
from benchmark_features import candles
from app.features.registry import STANDARD
from app.strategies.schemas import VersionCreate
from app.backtesting.schemas import RunCreate
from app.backtesting.engine import simulate

if __name__ == "__main__":
    definition = VersionCreate(
        trade_direction="CALL",
        indicator_specs=STANDARD,
        condition_tree={
            "left": {"type": "FIELD", "field": "rsi_14", "bars_ago": 0},
            "operator": "GTE",
            "right": {"type": "NUMBER", "value": "50"},
        },
    )
    config = RunCreate(
        strategy_version_id=1,
        dataset={"source": "BENCHMARK", "broker": "SYNTHETIC", "symbol": "TEST", "market_type": "REGULAR", "timeframe": "1m"},
        signal_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        signal_end=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=100000),
        payout_percent="83.5",
        expiry_bars=1,
        overlap_policy="ALLOW",
    )
    result = simulate(candles(100000), definition, config, max_trades=100000)
    print(
        dict(
            platform=platform.platform(),
            processor=platform.processor(),
            logical_cpus=os.cpu_count(),
            python=platform.python_version(),
            candles=100000,
            indicator_set="STANDARD",
            strategy="rsi_14>=50 CALL",
            timings=result["timings"],
            trades=result["metrics"]["trades_executed"],
            context="single process; synthetic generation included; no SQL/JSON; pure-engine trade cap100000; not an SLA",
        )
    )
