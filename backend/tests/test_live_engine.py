from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from app.live.features import IncrementalFeatures
from app.features.engine import compute
from app.features.registry import STANDARD
from app.live.providers import ReplayLiveProvider, ProviderFrame, MockLiveProvider, IQOptionReadOnlyProvider
from app.live.paper import PaperObservation
from app.backtesting.engine import simulate
from app.strategies.dsl import evaluate, Truth
from app.market_data.normalization import Dataset
from backtest_fixture import definition, config, candles, BASE, leaf
from feature_fixture import series, META


def test_10000_live_features_exactly_equal_frozen_batch():
    rows = series(values=[Decimal(100) + Decimal((i * 17) % 101) / 10 for i in range(10000)])
    rows = [
        replace(
            c,
            open_time=c.open_time + timedelta(minutes=2 if i >= 5000 else 0),
            close_time=c.close_time + timedelta(minutes=2 if i >= 5000 else 0),
        )
        for i, c in enumerate(rows)
    ]
    state = IncrementalFeatures(STANDARD)
    actual = [state.update(c) for c in rows]
    assert actual == list(compute(rows, STANDARD))
    assert len(state.rows) == 51 and len(state.pending) == 0


def test_replay_signals_and_paper_equal_frozen_backtest():
    rows = candles()
    d = definition()
    cfg = config(signal_start=rows[1].close_time, signal_end=rows[-1].close_time + timedelta(microseconds=1))
    expected = []
    result = simulate(rows, d, cfg, observe_signal=lambda cid, truth: expected.append(cid) if truth == Truth.TRUE else None)
    provider = ReplayLiveProvider(rows, initial=1, payout=Decimal("83.5"))
    state = IncrementalFeatures(d.indicator_specs)
    for c in provider.bootstrap(Dataset(**META)):
        state.update(c)
    signals, pending, outcomes = [], [], []
    for _ in rows[1:]:
        frame = provider.poll(Dataset(**META))
        assert frame.mode == "REPLAY" and frame.forming is None
        c = frame.closed[0]
        still = []
        for p in pending:
            out = p.update(c)
            if out:
                outcomes.append(out)
            else:
                still.append(p)
        pending = still
        row = state.update(c)
        truth, _ = evaluate(d.condition_tree, state.rows, row["close_time"])
        if truth == Truth.TRUE:
            signals.append(c.candle_id)
            pending.append(PaperObservation(c.candle_id, c, "CALL", 1, Decimal("83.5"), "PROVIDER"))
    assert signals == expected
    assert [o["result"] for o in outcomes] == [t["result"] for t in result["trades"]]
    assert [o["unit_pnl"] for o in outcomes] == [t["unit_pnl"] for t in result["trades"]]


def test_paper_gap_and_bearish_is_not_put_win():
    rows = candles([(99, 100), (102, 101)])
    p = PaperObservation(1, rows[0], "PUT", 1, Decimal("84"), "FIXED_ASSUMPTION")
    # Actual entry102 -> expiry101 wins for PUT, never infer outcome from signal candle colour.
    assert p.update(rows[1])["result"] == "WIN"
    p = PaperObservation(2, rows[0], "CALL", 1, Decimal("84"), "FIXED_ASSUMPTION")
    assert p.update(replace(rows[1], open_time=BASE + timedelta(minutes=2), close_time=BASE + timedelta(minutes=3)))["result"] == "GAP"


def test_mock_forming_contract_and_disabled_iq():
    p = MockLiveProvider([], [ProviderFrame(BASE, forming=candles()[0])])
    assert p.poll(Dataset(**META)).closed == ()
    assert not any(IQOptionReadOnlyProvider.capabilities.values())
    assert not any(hasattr(p, name) for name in ("buy", "sell", "place_order", "call", "put"))
