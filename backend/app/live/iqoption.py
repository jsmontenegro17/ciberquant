"""Read-only IQ provider; optional upstream stays private in its dedicated event loop."""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from threading import Thread
from time import monotonic
from ..features.engine import FeatureCandle
from ..market_data.normalization import Dataset, utc
from ..market_data.quality import validate_candle
from ..market_data.timeframe import duration
from .providers import CAPABILITIES, ProviderFrame
from .conflicts import DataConflictError

UPSTREAM_SHA = "acac6e08333466ae188c7dfa7fd2a03174e34ca2"


def exact_number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("IQ_NON_DECIMAL_NUMBER")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("IQ_NON_FINITE_NUMBER")
    return result


def map_assets(metadata, product):
    if product not in ("turbo", "binary"):
        raise ValueError("IQ_PRODUCT_UNSUPPORTED")
    result = {}
    for active_id, raw in metadata[product]["actives"].items():
        name = raw["name"].removeprefix("front.").upper()
        if not name:
            raise ValueError("IQ_UNKNOWN_ASSET")
        opened = raw.get("enabled") is True and raw.get("is_suspended") is False
        commission = raw.get("option", {}).get("profit", {}).get("commission")
        payout = Decimal(100) - exact_number(commission) if commission is not None else None
        if payout is not None and not 0 < payout <= 100:
            payout = None
        market = "OTC" if name.endswith("-OTC") else "REGULAR"
        item = dict(
            active_id=int(active_id), symbol=name, market_type=market, open=opened, payout=payout if opened else None, product=product
        )
        if name in result and result[name]["active_id"] != item["active_id"]:
            raise ValueError("IQ_AMBIGUOUS_ASSET")
        result[name] = item
    return result


def normalize_candle(raw, dataset, active_id):
    seconds = int(duration(dataset.timeframe).total_seconds())
    if raw.get("active_id", active_id) != active_id or raw.get("size", seconds) != seconds:
        raise ValueError("IQ_STREAM_IDENTITY_MISMATCH")
    start, end = exact_number(raw["from"]), exact_number(raw["to"])
    if start != int(start) or end != int(end) or end - start != seconds:
        raise ValueError("IQ_CANDLE_TIME_MISMATCH")
    candle = FeatureCandle(
        **dataset.model_dump(),
        open_time=datetime.fromtimestamp(int(start), timezone.utc),
        close_time=datetime.fromtimestamp(int(end), timezone.utc),
        open=exact_number(raw["open"]),
        high=exact_number(raw["max"]),
        low=exact_number(raw["min"]),
        close=exact_number(raw["close"]),
        # IQ "volume" can be fractional traded quantity, not a verified tick count.
        # Do not relabel it as tick_volume or round it to fit raw Numeric(24,10).
        tick_volume=None,
        spread=None,
    )
    if validate_candle(candle):
        raise ValueError("IQ_INVALID_CANDLE")
    return candle


class IQOptionReadOnlyProvider:
    capabilities = {k: False for k in CAPABILITIES}

    def __init__(
        self,
        *,
        email="",
        password="",
        ssid="",
        balance="PRACTICE",
        product="turbo",
        origin=None,
        max_history=250000,
        timeout=15,
        transport_factory=None,
        history_observer=None,
    ):
        if balance != "PRACTICE":
            raise ValueError("IQ_PRACTICE_REQUIRED")
        if product not in ("turbo", "binary"):
            raise ValueError("IQ_PRODUCT_UNSUPPORTED")
        self.capabilities = dict(type(self).capabilities)
        self._origin = utc(origin) if origin is not None else None
        self._max_history, self._timeout, self._product = max_history, timeout, product
        self._mapping = {}
        self._last = {}
        self._metadata_at = 0
        self._closed = False
        self._history_observer = history_observer
        if transport_factory is None:
            from .iq_transport import IQTransport

            transport_factory = IQTransport
        self._transport = transport_factory(email, password, ssid, balance, timeout)
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._loop.run_forever, name="cq-iq-read-only", daemon=True)
        self._thread.start()
        self._status = {}
        try:
            self._status = self._call(self._transport.connect())
            self._refresh()
        except BaseException:
            self.close()
            raise

    def _call(self, coro):
        async def bounded():
            return await asyncio.wait_for(coro, self._timeout)

        future = asyncio.run_coroutine_threadsafe(bounded(), self._loop)
        try:
            return future.result(timeout=self._timeout + 2)
        except Exception as exc:
            future.cancel()
            from .iq_transport import IQError

            if isinstance(exc, IQError):
                raise ConnectionError(str(exc)) from None
            raise ConnectionError("IQ_OPERATION_FAILED_" + type(exc).__name__) from None

    async def _clock(self):
        return self._transport.server_seconds()

    def _refresh(self):
        self._mapping = map_assets(self._call(self._transport.metadata()), self._product)
        self._metadata_at = monotonic()
        self.capabilities.update(assets=True, market_status=True)

    @property
    def status_metadata(self):
        return {
            **self._status,
            "integration": "UNOFFICIAL COMMUNITY INTEGRATION",
            "product": self._product,
            "upstream_sha": UPSTREAM_SHA,
            "capabilities": dict(self.capabilities),
        }

    def asset_status(self):
        if monotonic() - self._metadata_at > 5:
            self._refresh()
        return list(self._mapping.values())

    def assets(self):
        return [
            Dataset(source="IQOPTION", broker="IQOPTION", symbol=a["symbol"], market_type=a["market_type"], timeframe="1m")
            for a in self.asset_status()
        ]

    def _asset(self, dataset):
        if monotonic() - self._metadata_at > 5:
            self._refresh()
        asset = self._mapping.get(dataset.symbol)
        if dataset.source != "IQOPTION" or dataset.broker != "IQOPTION" or asset is None or dataset.market_type != asset["market_type"]:
            raise ValueError("IQ_UNKNOWN_OR_MISMATCHED_DATASET")
        return asset

    def _server_time(self):
        seconds = self._call(self._clock())
        self.capabilities["server_time"] = True
        # IQ timeSync is milliseconds. datetime precision is microseconds; integer construction.
        return datetime.fromtimestamp(int(seconds), timezone.utc)

    def recent_closed(self, dataset, count=20):
        asset = self._asset(dataset)
        now = self._server_time()
        step = int(duration(dataset.timeframe).total_seconds())
        raw = self._history(dataset, asset, step, min(count + 2, 1000), int(now.timestamp()), now, "RECENT")
        candles = [normalize_candle(r, dataset, asset["active_id"]) for r in raw]
        closed = sorted((c for c in candles if c.close_time <= now), key=lambda c: c.open_time)
        if closed:
            self.capabilities["historical_candles"] = True
        return closed[-count:]

    def _history(self, dataset, asset, step, count, end, clock, phase):
        raw = self._call(self._transport.history(asset["active_id"], step, count, end))
        if self._history_observer is not None:
            exact_clock = self._call(self._clock())
            response_clock = datetime.fromtimestamp(int(exact_clock), timezone.utc) + timedelta(
                microseconds=int((exact_clock - int(exact_clock)) * 1000000)
            )
            # Opt-in local diagnostics only. Explicit projection, never raw frames/auth.
            self._history_observer(
                dataset,
                [normalize_candle(r, dataset, asset["active_id"]) for r in raw],
                dict(
                    provider="IQOPTION",
                    product=self._product,
                    active_id=asset["active_id"],
                    history_request_end=end,
                    history_request_count=count,
                    phase=phase,
                    provider_time=clock,
                    provider_response_time=response_clock,
                    received_time=datetime.now(timezone.utc),
                ),
            )
        return raw

    def bootstrap(self, dataset):
        asset = self._asset(dataset)
        if self._origin is None:
            raise ValueError("IQ_CANONICAL_ORIGIN_REQUIRED")
        end = int(self._server_time().timestamp())
        cutoff = end
        step = int(duration(dataset.timeframe).total_seconds())
        rows = {}
        while True:
            raw = self._history(dataset, asset, step, 1000, end, datetime.fromtimestamp(cutoff, timezone.utc), "BOOTSTRAP")
            if not raw:
                raise ValueError("IQ_CANONICAL_HISTORY_UNAVAILABLE")
            batch = [normalize_candle(r, dataset, asset["active_id"]) for r in raw]
            earliest = min(c.open_time for c in batch)
            for c in batch:
                if c.open_time >= self._origin and c.close_time.timestamp() <= cutoff:
                    old = rows.get(c.open_time)
                    if old is not None and old != c:
                        raise DataConflictError(
                            dataset, old, c, phase="BOOTSTRAP", detection_layer="PROVIDER_BOOTSTRAP_INTERNAL", provider="IQOPTION"
                        )
                    rows[c.open_time] = c
            if len(rows) > self._max_history:
                raise ValueError("IQ_HISTORY_CAP_EXCEEDED")
            if earliest <= self._origin:
                break
            next_end = int(earliest.timestamp()) - 1
            if next_end >= end:
                raise ValueError("IQ_HISTORY_NO_PROGRESS")
            end = next_end
        ordered = sorted(rows.values(), key=lambda c: c.open_time)
        if not ordered or ordered[0].open_time != self._origin:
            raise ValueError("IQ_CANONICAL_ORIGIN_UNAVAILABLE")
        self._last[dataset] = ordered[-1].open_time
        self.capabilities["historical_candles"] = True
        self._call(self._transport.start_stream(asset["active_id"], step))
        return ordered

    def poll(self, dataset):
        asset = self._asset(dataset)
        now = self._server_time()
        step = int(duration(dataset.timeframe).total_seconds())
        if dataset not in self._last:
            raise ValueError("IQ_BOOTSTRAP_REQUIRED")
        # Closed values are confirmed through history; never freeze the final observed forming tick.
        count = int((now - self._last[dataset]).total_seconds() // step) + 2
        if count > 1000:
            raise ValueError("IQ_RECONNECT_BOOTSTRAP_REQUIRED")
        rows = self._history(dataset, asset, step, max(3, count), int(now.timestamp()), now, "OBSERVED")
        closed = tuple(
            sorted(
                (
                    c
                    for c in (normalize_candle(r, dataset, asset["active_id"]) for r in rows)
                    if c.close_time <= now and c.open_time >= self._last[dataset]
                ),
                key=lambda c: c.open_time,
            )
        )

        async def latest():
            return self._transport.latest(asset["active_id"], step)

        update = self._call(latest())
        forming = None
        if update is not None:
            c = normalize_candle(update, dataset, asset["active_id"])
            self.capabilities["live_candles"] = True
            if c.open_time <= now < c.close_time:
                forming = c
                self.capabilities["forming_candle"] = True
        if closed:
            self._last[dataset] = closed[-1].open_time
        if asset["payout"] is not None:
            self.capabilities["payout"] = True
        return ProviderFrame(now, closed, forming, asset["payout"], asset["open"])

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._call(self._transport.close())
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=3)
            if not self._thread.is_alive():
                self._loop.close()
