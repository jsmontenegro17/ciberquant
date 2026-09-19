from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from backtest_fixture import candles, definition, BASE
from feature_fixture import META
from app.validation.schemas import ValidationCreate


def data(size=1500, losing_test=False):
    template = candles()[0]
    # 24 contiguous hourly candles/day; test has >10 days, >=100 resolved, each fold >20.
    return [
        replace(
            template,
            candle_id=i + 1,
            timeframe="1h",
            open_time=BASE + timedelta(hours=i),
            close_time=BASE + timedelta(hours=i + 1),
            open=Decimal(100),
            high=Decimal(102),
            low=Decimal(98),
            close=Decimal(99 if losing_test and i >= size * 4 // 5 else 101),
        )
        for i in range(size)
    ]


def request(size=1500, **changes):
    return ValidationCreate(
        **{
            **dict(
                strategy_version_id=1,
                dataset={**META, "timeframe": "1h"},
                overall_start=BASE,
                overall_end=BASE + timedelta(hours=size),
                payout_percent="83.5",
                expiry_bars=1,
            ),
            **changes,
        }
    )


def create_strategy(client):
    strategy = client.post("/api/v1/strategies", json={"name": "Fixed validation fixture"}).json()
    sid = strategy["id"]
    version = client.post(f"/api/v1/strategies/{sid}/versions", json=definition().model_dump(mode="json")).json()
    client.patch(f"/api/v1/strategies/{sid}", json={"status": "TESTING"})
    return sid, version["id"]
