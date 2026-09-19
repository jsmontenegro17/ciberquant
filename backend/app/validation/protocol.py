"""Frozen cq-validation-v1 deterministic chronology and statistical evidence."""

from collections import defaultdict
from decimal import Decimal, localcontext
from hashlib import sha256
from ..features.serialization import CALC_CONTEXT
from ..backtesting.metrics import summarize
from ..market_data.normalization import stored_utc
from . import VALIDATION_ENGINE_VERSION


def definitions():
    return dict(
        validation_engine_version=VALIDATION_ENGINE_VERSION,
        feature_engine_version="cq-features-v1",
        strategy_dsl_version="cq-strategy-dsl-v1",
        backtest_engine_version="cq-binary-backtest-v1",
        split=[60, 20, 20],
        fold_count=4,
        minimum_candles=20,
        minimum_resolved=100,
        minimum_active_days=10,
        minimum_fold_resolved=20,
        minimum_evaluable_folds=3,
        minimum_positive_folds=3,
        bootstrap=dict(
            iterations=2000,
            blocks="UTC signal day",
            metric="mean unit P&L per executed trade",
            percentiles=["0.025", "0.975"],
            rng="SHA256 counter/rejection v1",
        ),
        verdict_gates=[
            "test_resolved",
            "test_days",
            "evaluable_folds",
            "positive_folds",
            "validation_edge",
            "test_edge",
            "test_pnl",
            "bootstrap_lower",
        ],
    )


def split(candles, start, end):
    selected = [c for c in candles if start <= c.open_time < end]
    if len(selected) < 20:
        raise ValueError("At least 20 snapshot candles required")
    if any(a.open_time >= b.open_time or a.close_time >= b.close_time for a, b in zip(selected, selected[1:])):
        raise ValueError("Non-increasing snapshot chronology")
    n = len(selected)
    a, b = 3 * n // 5, 4 * n // 5
    va, te = selected[a].open_time, selected[b].open_time
    parts = [("TRAIN", 0, start, va), ("VALIDATION", 0, va, te), ("TEST", 0, te, end)]
    for k in range(4):
        lo = selected[a + k * (b - a) // 4].open_time
        hi = te if k == 3 else selected[a + (k + 1) * (b - a) // 4].open_time
        parts.append(("WALK_FORWARD", k + 1, lo, hi))
    return parts


def bootstrap(trades, config_hash):
    blocks = defaultdict(lambda: [Decimal(0), 0])
    for t in trades:
        block = blocks[stored_utc(t["signal_time"]).date().isoformat()]
        block[0] += t["unit_pnl"]
        block[1] += 1
    ordered = [blocks[k] for k in sorted(blocks)]
    count, counter = len(ordered), 0
    seed = sha256(("cq-validation-v1:" + config_hash).encode()).hexdigest()
    result = dict(seed=seed, iterations=2000, block_count=count, point_estimate=None, lower_95=None, upper_95=None)
    if not count:
        return result
    cutoff = (2**256 // count) * count

    def draw():
        nonlocal counter
        while True:
            value = int.from_bytes(sha256(bytes.fromhex(seed) + counter.to_bytes(16, "big")).digest(), "big")
            counter += 1
            if value < cutoff:
                return ordered[value % count]

    with localcontext(CALC_CONTEXT):
        estimates = []
        for _ in range(2000):
            total, size = Decimal(0), 0
            for _ in range(count):
                pnl, n = draw()
                total += pnl
                size += n
            estimates.append(total / size)
        estimates.sort()

        def percentile(p):
            index = Decimal(len(estimates) - 1) * p
            i = int(index)
            return estimates[i] + (estimates[min(i + 1, len(estimates) - 1)] - estimates[i]) * (index - i)

        result.update(
            point_estimate=sum(b[0] for b in ordered) / sum(b[1] for b in ordered),
            lower_95=percentile(Decimal(".025")),
            upper_95=percentile(Decimal(".975")),
        )
    return result


def verdict(validation, folds, test, boot):
    evaluable = [f for f in folds if f["resolved_trades"] >= 20]
    positive = lambda x: x is not None and Decimal(str(x)) > 0
    gates = dict(
        test_resolved=test["resolved_trades"] >= 100,
        test_days=boot["block_count"] >= 10,
        evaluable_folds=len(evaluable) >= 3,
        positive_folds=sum(positive(f["total_unit_pnl"]) for f in evaluable) >= 3,
        validation_edge=positive(validation["edge_percentage_points"]),
        test_edge=positive(test["edge_percentage_points"]),
        test_pnl=positive(test["total_unit_pnl"]),
        bootstrap_lower=positive(boot["lower_95"]),
    )
    sufficient = all(gates[k] for k in ("test_resolved", "test_days", "evaluable_folds"))
    return ("INCONCLUSIVE" if not sufficient else "PASS" if all(gates.values()) else "FAIL"), gates


def monthly(trades, payout):
    groups = defaultdict(list)
    for t in trades:
        groups[stored_utc(t["signal_time"]).strftime("%Y-%m")].append(t)
    return [{"month": k, **summarize(groups[k], payout, {})[0]} for k in sorted(groups)]


def historical_state(runs):
    completed = sorted(
        [r for r in runs if r.status == "COMPLETED"],
        key=lambda r: (stored_utc(r.test_end), stored_utc(r.test_start), stored_utc(r.created_at), r.id),
    )
    seen, state = False, "NOT_VALIDATED"
    hashes = set()
    for r in completed:
        if r.config_sha256 in hashes:
            continue
        hashes.add(r.config_sha256)
        if r.verdict == "PASS":
            seen, state = True, "HISTORICALLY_VALIDATED"
        elif r.verdict == "FAIL" and seen:
            state = "DEGRADED"
    return state
