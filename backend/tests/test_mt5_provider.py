from datetime import datetime, timezone, timedelta
from decimal import Decimal
from types import SimpleNamespace
import pytest
from app.live.mt5 import MetaTrader5Provider
from app.market_data.normalization import Dataset


class ReadOnlySDK:
    TIMEFRAME_M1 = 1

    def __init__(self, origin):
        self.origin = origin
        self.closed = False

    def initialize(self):
        return True

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def account_info(self):
        return SimpleNamespace(server="BROKER")

    def symbols_get(self):
        return [SimpleNamespace(name="EURUSD")]

    def copy_rates_range(self, symbol, timeframe, start, end):
        assert start.tzinfo is not None and end.tzinfo is not None
        return [dict(time=int(self.origin.timestamp()), open=1.1, high=1.2, low=1.0, close=1.15, tick_volume=10, spread=2)]

    def shutdown(self):
        self.closed = True


def test_mt5_optional_read_only_utc_decimal_identity_and_origin():
    origin = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=2)
    sdk = ReadOnlySDK(origin)
    provider = MetaTrader5Provider("BROKER", origin, sdk=sdk)
    dataset = Dataset(source="MT5", broker="BROKER", symbol="EURUSD", market_type="REGULAR", timeframe="1m")
    assert provider.assets() == [dataset]
    row = provider.bootstrap(dataset)[0]
    assert row.open == Decimal("1.1") and row.open_time == origin
    assert provider.poll(dataset).closed == (row,)
    with pytest.raises(ValueError):
        provider.bootstrap(dataset.model_copy(update={"market_type": "OTC"}))
    with pytest.raises(ValueError):
        provider.bootstrap(dataset.model_copy(update={"broker": "OTHER"}))
    provider.origin = origin - timedelta(minutes=1)
    with pytest.raises(ValueError, match="INSUFFICIENT_HISTORY"):
        provider.bootstrap(dataset)
    provider.close()
    assert sdk.closed
