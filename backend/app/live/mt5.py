"""Optional terminal-local adapter: imports SDK only when explicitly constructed."""

import importlib
from datetime import datetime, timezone
from decimal import Decimal
from ..features.engine import FeatureCandle
from ..market_data.timeframe import duration
from ..market_data.normalization import Dataset, utc
from .providers import CAPABILITIES, ProviderFrame


class MetaTrader5Provider:
    capabilities = {**CAPABILITIES, "server_time": False, "market_status": False}

    def __init__(self, broker, origin, max_history=250000, sdk=None):
        self.broker, self.origin, self.max_history = broker, utc(origin), max_history
        self.sdk = sdk if sdk is not None else importlib.import_module("MetaTrader5")
        if not self.sdk.initialize():
            raise ConnectionError("MT5 terminal unavailable")

    def assets(self):
        return [
            Dataset(source="MT5", broker=self.broker, symbol=s.name, market_type="REGULAR", timeframe="1m")
            for s in (self.sdk.symbols_get() or ())
        ]

    def _rates(self, dataset, start, end):
        if dataset.source != "MT5" or dataset.broker != self.broker.upper() or dataset.market_type != "REGULAR":
            raise ValueError("MT5 dataset identity mismatch; OTC unsupported")
        mapping = {"1m": "TIMEFRAME_M1", "5m": "TIMEFRAME_M5", "15m": "TIMEFRAME_M15", "30m": "TIMEFRAME_M30", "1h": "TIMEFRAME_H1"}
        info = self.sdk.terminal_info()
        if info is None or not info.connected:
            raise ConnectionError("MT5 disconnected")
        account = self.sdk.account_info()
        if account is None or account.server.upper() != self.broker.upper():
            raise ConnectionError("Configured broker does not match terminal server")
        rates = self.sdk.copy_rates_range(dataset.symbol, getattr(self.sdk, mapping[dataset.timeframe]), start, end)
        if rates is None or len(rates) > self.max_history:
            raise ConnectionError("MT5 history unavailable or configured cap exceeded")
        return [
            FeatureCandle(
                **dataset.model_dump(),
                open_time=datetime.fromtimestamp(int(r["time"]), timezone.utc),
                close_time=datetime.fromtimestamp(int(r["time"]), timezone.utc) + duration(dataset.timeframe),
                **{k: Decimal(str(r[k])) for k in ("open", "high", "low", "close", "tick_volume", "spread")},
            )
            for r in rates
        ]

    def bootstrap(self, dataset):
        now = datetime.now(timezone.utc)
        rows = [c for c in self._rates(dataset, self.origin, now) if c.close_time <= now]
        # No silently truncated recursive seed: the configured canonical origin must be present.
        if not rows or rows[0].open_time != self.origin:
            raise ValueError("INSUFFICIENT_HISTORY: configured canonical origin unavailable")
        self.last = rows[-1].open_time
        return rows

    def poll(self, dataset):
        now = datetime.now(timezone.utc)
        rows = self._rates(dataset, self.last, now)
        closed = tuple(c for c in rows if c.close_time <= now)
        forming = next((c for c in rows if c.open_time <= now < c.close_time), None)
        if closed:
            self.last = closed[-1].open_time
        # SDK does not provide a trusted broker server clock. Local UTC is explicitly labelled below.
        return ProviderFrame(now, closed, forming, market_open=None)

    def close(self):
        self.sdk.shutdown()
