from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from feature_fixture import series, BASE, META
from app.strategies.schemas import VersionCreate
from app.backtesting.schemas import RunCreate


def field(name="close", ago=0):
    return {"type": "FIELD", "field": name, "bars_ago": ago}


def leaf(name="close", operator="GT", value="0", kind="NUMBER", ago=0):
    return {"left": field(name, ago), "operator": operator, "right": {"type": kind, "value": value}}


def definition(tree=None, direction="CALL", specs=None):
    return VersionCreate(trade_direction=direction, indicator_specs=specs or [], condition_tree=tree or leaf())


def config(**kwargs):
    data = dict(
        strategy_version_id=1,
        dataset=META,
        signal_start=BASE,
        signal_end=BASE + timedelta(minutes=20),
        payout_percent="83.5",
        expiry_bars=1,
    )
    return RunCreate(**{**data, **kwargs})


def candles(pairs=None):
    pairs = pairs or [(99, 100), (105, 106), (102, 101), (101, 101), (101, 99), (99, 100)]
    return [
        replace(c, open=Decimal(str(o)), close=Decimal(str(v)), high=Decimal(max(o, v) + 1), low=max(Decimal(".1"), Decimal(min(o, v) - 1)))
        for c, (o, v) in zip(series(size=len(pairs)), pairs)
    ]
