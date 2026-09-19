"""Causal bounded-state loop: open -> settlement -> close signal -> schedule."""

from collections import deque
from dataclasses import asdict
from decimal import Decimal
from time import perf_counter
from ..features.engine import compute
from ..market_data.timeframe import duration
from ..strategies.dsl import evaluate, Truth
from .outcome import resolve
from .metrics import summarize

SKIPS = ("unavailable", "entry_gap", "expiry_gap", "outside_range", "overlap", "no_future_data")


def simulate(candles, definition, config, max_source=250000, max_trades=10000, observe_signal=None):
    history, active, trades = deque(maxlen=51), [], []
    pending, previous_close, step = None, None, None
    counters = {f"skipped_{key}": 0 for key in SKIPS}
    counters.update(candles_processed=0, candidates_evaluated=0, signals_true=0)
    timing = dict(feature_calculation=0.0, signal_evaluation=0.0, execution_simulation=0.0)
    start_clock = perf_counter()

    def skip(reason):
        counters[f"skipped_{reason}"] += 1

    def source():
        nonlocal step
        for c in candles:
            if c.open_time >= config.signal_end:
                break
            if step is None:
                step = duration(c.timeframe)
            yield c

    features = iter(compute(source(), definition.indicator_specs))
    while True:
        mark = perf_counter()
        try:
            row = next(features)
        except StopIteration:
            break
        timing["feature_calculation"] += perf_counter() - mark
        mark = perf_counter()
        counters["candles_processed"] += 1
        if counters["candles_processed"] > max_source:
            raise ValueError("BACKTEST_MAX_SOURCE_CANDLES exceeded; no truncation")
        opened, closed = row["open_time"], row["close_time"]
        if previous_close is not None and closed <= previous_close:
            raise ValueError("Non-increasing close times in execution dataset")
        if pending is not None:
            if opened != pending["expected_open"] or opened < pending["signal_time"]:
                skip("entry_gap")
            else:
                active.append(
                    {
                        **pending,
                        "entry_candle_id": row["candle_id"],
                        "entry_time": opened,
                        "entry_price": row["open"],
                        "remaining": config.expiry_bars,
                        "next_open": opened,
                        "previous_close": pending["signal_time"],
                    }
                )
            pending = None
        still_open = []
        for trade in active:
            if opened != trade["next_open"] or opened < trade["previous_close"]:
                skip("expiry_gap")
                continue
            if closed > config.signal_end:
                skip("outside_range")
                continue
            trade["remaining"] -= 1
            if trade["remaining"] == 0:
                outcome = resolve(
                    definition.trade_direction,
                    trade["entry_time"],
                    trade["entry_price"],
                    closed,
                    row["close"],
                    Decimal(config.payout_percent),
                )
                trades.append(
                    {
                        **asdict(outcome),
                        "signal_candle_id": trade["signal_candle_id"],
                        "entry_candle_id": trade["entry_candle_id"],
                        "expiry_candle_id": row["candle_id"],
                        "signal_time": trade["signal_time"],
                        "signal_context": trade["signal_context"],
                        "payout_percent": Decimal(config.payout_percent),
                        "sequence_no": len(trades) + 1,
                    }
                )
                if len(trades) > max_trades:
                    raise ValueError("BACKTEST_MAX_TRADES exceeded; no truncation")
            else:
                trade.update(next_open=opened + step, previous_close=closed)
                still_open.append(trade)
        active = still_open
        timing["execution_simulation"] += perf_counter() - mark
        history.append(row)
        if config.signal_start <= closed < config.signal_end:
            counters["candidates_evaluated"] += 1
            mark = perf_counter()
            truth, context = evaluate(definition.condition_tree, history, closed)
            timing["signal_evaluation"] += perf_counter() - mark
            if observe_signal:
                observe_signal(row["candle_id"], truth)
            if truth == Truth.UNKNOWN:
                skip("unavailable")
            elif truth == Truth.TRUE:
                counters["signals_true"] += 1
                if config.overlap_policy == "SKIP_UNTIL_EXPIRY" and active:
                    skip("overlap")
                elif opened + step >= config.signal_end:
                    skip("outside_range")
                else:
                    pending = dict(
                        signal_candle_id=row["candle_id"], signal_time=closed, signal_context=context, expected_open=opened + step
                    )
        previous_close = closed
    if pending:
        skip("outside_range" if pending["expected_open"] >= config.signal_end else "no_future_data")
    for trade in active:
        skip("outside_range" if trade["next_open"] + step * trade["remaining"] > config.signal_end else "no_future_data")
    metrics, curve = summarize(trades, Decimal(config.payout_percent), counters)
    timing["total"] = perf_counter() - start_clock
    return dict(metrics=metrics, trades=trades, equity_curve=curve, timings=timing)
