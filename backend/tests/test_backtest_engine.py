from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.backtesting.outcome import resolve
from app.backtesting.engine import simulate
from app.backtesting.metrics import summarize
from app.features.engine import compute
from app.strategies.dsl import evaluate, Truth, digest
from backtest_fixture import candles, config, definition, leaf, field, BASE


@pytest.mark.parametrize(
    "direction,price,result",
    [("CALL", 101, "WIN"), ("CALL", 99, "LOSS"), ("CALL", 100, "DRAW"), ("PUT", 101, "LOSS"), ("PUT", 99, "WIN"), ("PUT", 100, "DRAW")],
)
def test_binary_outcome_exact(direction, price, result):
    outcome = resolve(direction, BASE, Decimal(100), BASE + timedelta(minutes=1), Decimal(price), Decimal("83.5"))
    assert outcome.result == result
    assert outcome.unit_pnl == {"WIN": Decimal(".835"), "LOSS": Decimal(-1), "DRAW": Decimal(0)}[result]


def test_next_open_not_signal_close_and_timing():
    result = simulate(candles(), definition(), config())
    t = result["trades"][0]
    assert t["entry_price"] == 105 and t["entry_price"] != 100
    assert t["signal_time"] == t["entry_time"] == BASE + timedelta(minutes=1)
    assert t["expiry_time"] == BASE + timedelta(minutes=2)
    assert t["expiry_price"] == 106 and t["result"] == "WIN"
    assert all(t["entry_time"] >= t["signal_time"] for t in result["trades"])


def test_bearish_expiry_not_put_win_and_two_bars():
    data = candles([(99, 100), (100, 103), (102, 101)])
    result = simulate(data, definition(direction="PUT"), config(expiry_bars=2))
    t = result["trades"][0]
    assert t["entry_price"] == 100 and t["expiry_price"] == 101
    assert t["expiry_time"] == BASE + timedelta(minutes=3) and t["result"] == "LOSS"
    assert data[2].close < data[2].open


def test_entry_and_expiry_gaps_never_fabricate_trades():
    data = candles()
    gap = data[:1] + data[2:]
    result = simulate(gap, definition(leaf("close", "EQ", "100")), config())
    assert result["metrics"]["skipped_entry_gap"] == 1
    gap = data[:2] + data[3:]
    result = simulate(gap, definition(leaf("close", "EQ", "100")), config(expiry_bars=2))
    assert result["metrics"]["skipped_expiry_gap"] == 1 and not result["trades"]


def test_availability_rejects_entry_before_signal_close():
    data = candles()
    data[0] = replace(data[0], close_time=BASE + timedelta(seconds=90))
    result = simulate(data, definition(leaf("close", "EQ", "100")), config())
    assert result["metrics"]["skipped_entry_gap"] == 1
    assert not any(t["signal_candle_id"] == data[0].candle_id for t in result["trades"])


def test_overlap_settles_before_same_time_new_signal():
    from feature_fixture import series

    data = series(size=20)
    a = simulate(data, definition(), config(expiry_bars=5))
    b = simulate(data, definition(), config(expiry_bars=5, overlap_policy="SKIP_UNTIL_EXPIRY"))
    assert len(a["trades"]) == 15 and len(b["trades"]) == 3
    assert b["metrics"]["skipped_overlap"] == 15
    assert b["trades"][1]["signal_time"] == b["trades"][0]["expiry_time"]


def test_range_boundary_and_no_future_data():
    data = candles()
    r = simulate(data[:2], definition(), config(signal_end=BASE + timedelta(minutes=2), expiry_bars=2))
    assert not r["trades"] and r["metrics"]["skipped_outside_range"] == 1
    r = simulate(data[:1], definition(), config())
    assert r["metrics"]["skipped_no_future_data"] == 1
    r = simulate(data[:2], definition(), config(signal_end=BASE + timedelta(minutes=2)))
    assert len(r["trades"]) == 1 and r["trades"][0]["expiry_time"] == config(signal_end=BASE + timedelta(minutes=2)).signal_end


def test_warmup_bars_ago_field_comparison_and_tristate():
    from feature_fixture import series

    d = definition(leaf("ema_50", "GT", "0"), specs=[{"type": "EMA", "period": 50}])
    r = simulate(series(size=60), d, config(signal_end=BASE + timedelta(minutes=60)))
    assert r["metrics"]["skipped_unavailable"] == 49
    ccc = {"operator": "AND", "conditions": [leaf("direction", "EQ", "C", "STRING", i) for i in range(3)]}
    data = candles([(1, 2)] * 5)
    r = simulate(data, definition(ccc), config())
    assert r["metrics"]["skipped_unavailable"] == 2 and r["trades"][0]["signal_candle_id"] == 3
    rows = list(compute(series(size=60), d.indicator_specs))
    ftf = {"left": field("close"), "operator": "GT", "right": field("ema_50")}
    assert (
        evaluate(definition(ftf, specs=[{"type": "EMA", "period": 50}]).condition_tree, rows[-51:], rows[-1]["close_time"])[0] == Truth.TRUE
    )
    unknown = leaf("ema_50", "GT", "0")
    false, true = leaf("close", "LT", "0"), leaf("close", "GT", "0")
    for op, child, expected in [
        ("AND", false, Truth.FALSE),
        ("AND", true, Truth.UNKNOWN),
        ("OR", true, Truth.TRUE),
        ("OR", false, Truth.UNKNOWN),
    ]:
        tree = definition({"operator": op, "conditions": [unknown, child]}, specs=d.indicator_specs).condition_tree
        assert evaluate(tree, rows[:1], rows[0]["close_time"])[0] == expected


def test_future_mutation_cannot_change_earlier_signals():
    from feature_fixture import series

    data = series(size=200)
    changed = data[:100] + [replace(c, open=c.open * 2, high=c.high * 2, low=c.low * 2, close=c.close * 2) for c in data[100:]]
    d = definition(leaf("rsi_14", "GTE", "70"), specs=[{"type": "RSI", "period": 14}])
    observations = []
    for rows in (data, changed):
        seen = []
        simulate(rows, d, config(signal_end=BASE + timedelta(minutes=201)), observe_signal=lambda i, t: seen.append((i, t)))
        observations.append(seen)
    assert observations[0][:100] == observations[1][:100]


def test_metrics_manual_draws_streaks_drawdown_and_null():
    results = ["WIN", "WIN", "DRAW", "LOSS", "LOSS", "WIN"]
    ts = [
        dict(
            result=r,
            unit_pnl={"WIN": Decimal(".835"), "LOSS": Decimal(-1), "DRAW": Decimal(0)}[r],
            expiry_time=BASE + timedelta(minutes=i + 1),
        )
        for i, r in enumerate(results)
    ]
    m, curve = summarize(ts, Decimal("83.5"), {})
    assert m["total_unit_pnl"] == Decimal(".505") and m["max_drawdown_units"] == 2
    assert m["max_win_streak"] == m["max_loss_streak"] == 2 and m["win_rate_percent"] == 60
    assert m["ev_per_resolved_trade"] == Decimal(".101") and m["gross_loss_units"] == 2
    assert curve[0]["equity"] == 0 and curve[-1]["equity"] == Decimal(".505")
    empty, _ = summarize([], Decimal(84), {})
    assert str(empty["break_even_win_rate_percent"]).startswith("54.347826086956")
    assert empty["win_rate_percent"] is None and empty["average_pnl_per_signal"] is None


@pytest.mark.parametrize(
    "tree",
    [
        leaf("unknown"),
        leaf("direction", "GT", "70"),
        leaf("close", "GT", 4),
        leaf("close", ago=-1),
        leaf("close", ago=51),
        {"operator": "AND", "conditions": []},
        {"operator": "OR", "conditions": [leaf()] * 51},
        {"operator": "EXEC", "code": "print(1)"},
        leaf("ema_20"),
    ],
)
def test_invalid_dsl(tree):
    with pytest.raises(ValidationError):
        definition(tree)


def test_depth_canonical_hash_and_limits():
    tree = leaf()
    for _ in range(4):
        tree = {"operator": "AND", "conditions": [tree]}
    with pytest.raises(ValidationError):
        definition(tree)
    assert digest(definition(leaf(value="1.00")).snapshot()) == digest(definition(leaf(value="1")).snapshot())
    for kw in [
        dict(expiry_bars=61),
        dict(expiry_bars=True),
        dict(payout_percent=83.5),
        dict(payout_percent="0"),
        dict(payout_percent="NaN"),
    ]:
        with pytest.raises(ValidationError):
            config(**kw)
    with pytest.raises(ValueError, match="SOURCE"):
        simulate(candles(), definition(), config(), max_source=1)
    with pytest.raises(ValueError, match="TRADES"):
        simulate(candles(), definition(), config(), max_trades=1)
