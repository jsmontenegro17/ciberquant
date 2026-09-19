import asyncio
import ast
import inspect
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
import pytest
from app.live.iqoption import IQOptionReadOnlyProvider, map_assets, normalize_candle, exact_number
from app.market_data.normalization import Dataset

pytest.importorskip("iqoptionapi")
from app.live.iq_transport import _ReadOnlySocket, _AsyncReadOnly, IQTransport, IQError, allowed_frame, parse_frame
from websockets.asyncio.server import serve

BASE = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)
META = Dataset(source="IQOPTION", broker="IQOPTION", symbol="EURUSD-OTC", market_type="OTC", timeframe="1m")


def raw(i=0):
    start = int(BASE.timestamp()) + i * 60
    return dict(
        active_id=42,
        size=60,
        **{"from": start, "to": start + 60},
        open="1.10001",
        close="1.10002",
        min="1.10",
        max="1.11",
        volume="3.12345678901234",
    )


def metadata():
    return {
        "turbo": {
            "actives": {
                "42": {"name": "front.EURUSD-OTC", "enabled": True, "is_suspended": False, "option": {"profit": {"commission": 15}}},
                "2": {"name": "front.EURUSD", "enabled": True, "is_suspended": True, "option": {"profit": {"commission": 20}}},
            }
        },
        "binary": {
            "actives": {
                "42": {"name": "front.EURUSD-OTC", "enabled": True, "is_suspended": False, "option": {"profit": {"commission": 21}}}
            }
        },
    }


def test_iq_identity_precision_and_product_mapping():
    mapping = map_assets(metadata(), "turbo")
    assert mapping["EURUSD-OTC"]["payout"] == 85
    assert mapping["EURUSD"]["open"] is False and mapping["EURUSD"]["payout"] is None
    assert map_assets(metadata(), "binary")["EURUSD-OTC"]["payout"] == 79
    candle = normalize_candle(raw(), META, 42)
    assert candle.open == Decimal("1.10001") and candle.close_time == BASE + timedelta(minutes=1)
    assert candle.tick_volume is None  # Traded quantity is not a tick count; do not round.
    assert parse_frame('{"price":1.1234567890}')["price"] == Decimal("1.1234567890")
    for bad in [1.23, True, float("nan")]:
        with pytest.raises(ValueError):
            exact_number(bad)
    with pytest.raises(ValueError):
        normalize_candle({**raw(), "active_id": 99}, META, 42)
    with pytest.raises(ValueError):
        normalize_candle({**raw(), "size": 300}, META, 42)
    with pytest.raises(ValueError):
        map_assets(metadata(), "digital")


def test_no_order_surface_and_wire_allowlist():
    forbidden = {
        "buy",
        "buy_digital_spot",
        "buy_digital_spot_v2",
        "buy_order",
        "sell_option",
        "close_position",
        "order_send",
        "place_order",
        "sell",
        "call",
        "put",
    }
    assert not any(hasattr(IQOptionReadOnlyProvider, k) for k in forbidden)
    assert not any(hasattr(IQTransport, k) for k in forbidden)
    for method in forbidden:
        assert not allowed_frame({"name": method, "msg": {}})
        assert not allowed_frame({"name": "sendMessage", "msg": {"name": method}})
    for module in ["iqoption.py", "iq_transport.py"]:
        tree = ast.parse((Path(inspect.getfile(IQOptionReadOnlyProvider)).parent / module).read_text())
        assert not [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in forbidden]
    with pytest.raises(ValueError):
        IQOptionReadOnlyProvider(balance="REAL")
    with pytest.raises(IQError):
        IQTransport("a", "b", balance="REAL")


class FakeTransport:
    def __init__(self, *args):
        self.index = 2
        self.fail = False
        self.closed = False

    async def connect(self):
        return {"authenticated": True, "profile_verified": True, "balance_mode": "PRACTICE"}

    async def metadata(self):
        return metadata()

    def server_seconds(self):
        if self.fail:
            raise IQError("IQ_DISCONNECTED")
        return Decimal(int(BASE.timestamp()) + self.index * 60 + 10)

    async def history(self, active, size, count, end):
        return [raw(i) for i in range(self.index + 1)]

    async def start_stream(self, active, size):
        pass

    def latest(self, active, size):
        return raw(self.index)

    async def close(self):
        self.closed = True


def test_provider_bootstrap_forming_closed_capabilities_and_disconnect():
    fake = FakeTransport()
    p = IQOptionReadOnlyProvider(origin=BASE, transport_factory=lambda *args: fake)
    try:
        assert not p.capabilities["live_candles"]
        assert len(p.assets()) == 2
        history = p.bootstrap(META)
        assert len(history) == 2
        frame = p.poll(META)
        assert frame.forming.open_time == BASE + timedelta(minutes=2)
        assert all(c.close_time <= frame.server_time for c in frame.closed)
        assert frame.payout == 85 and frame.market_open is True
        assert all(p.capabilities.values())
        fake.index = 3
        assert p.poll(META).closed[-1].open_time == BASE + timedelta(minutes=2)
        with pytest.raises(ValueError):
            p.bootstrap(META.model_copy(update={"market_type": "REGULAR"}))
        fake.fail = True
        with pytest.raises(ConnectionError, match="IQ_DISCONNECTED"):
            p.poll(META)
    finally:
        p.close()
    assert fake.closed and not p._thread.is_alive()


def test_fake_websocket_auth_decimal_metadata_stream_and_secret_redaction(caplog):
    caplog.set_level(logging.DEBUG)

    async def scenario():
        frames = []

        async def server(ws):
            async for encoded in ws:
                frame = json.loads(encoded)
                frames.append(frame)
                if frame["name"] == "authenticate":
                    await ws.send(json.dumps({"name": "authenticated", "msg": True}))
                    await ws.send(json.dumps({"name": "timeSync", "msg": int(BASE.timestamp()) * 1000}))
                elif frame["name"] == "sendMessage":
                    request = frame["msg"]["name"]
                    value = {}
                    if request == "get-profile":
                        value = {"id": "private-profile"}
                    elif request == "get-balances":
                        value = [{"id": 123, "type": 1}, {"id": 456, "type": 4}]
                    elif request == "get-initialization-data":
                        value = metadata()
                    elif request == "get-candles":
                        value = {"candles": [raw()]}
                    await ws.send(json.dumps({"name": "reply", "request_id": frame["request_id"], "msg": value}))
                elif frame["name"] == "subscribeMessage":
                    await ws.send('{"name":"candle-generated","msg":{"active_id":42,"size":60,"close":1.1234567890}}')

        silent = logging.Logger("fake.iq.server.disabled")
        silent.disabled = True
        async with serve(server, "127.0.0.1", 0, logger=silent) as listener:
            port = listener.sockets[0].getsockname()[1]
            t = IQTransport("email-secret", "password-secret", ssid="session-secret")
            t._client = _AsyncReadOnly("email-secret", "password-secret", "session-secret", 3, wss_url=f"ws://127.0.0.1:{port}")
            try:
                status = await t.connect()
                assert status == {"authenticated": True, "profile_verified": True, "balance_mode": "PRACTICE"}
                assert t._practice_id == 456
                assert await t.metadata() == metadata()
                assert len(await t.history(42, 60, 1, int(BASE.timestamp()))) == 1
                await t.start_stream(42, 60)
                for _ in range(30):
                    if t.latest(42, 60):
                        break
                    await asyncio.sleep(0.01)
                assert t.latest(42, 60)["close"] == Decimal("1.1234567890")
                assert t.server_seconds() == int(BASE.timestamp())
                with pytest.raises(IQError):
                    await t._client._ws._send_raw({"name": "buy", "msg": {}})
                assert all(allowed_frame(frame) for frame in frames)
            finally:
                await t.close()

    asyncio.run(scenario())
    assert not any(secret in caplog.text for secret in ("password-secret", "session-secret", "private-profile"))


def test_paginated_bootstrap_preserves_boundary_and_rejects_missing_origin():
    class Pages(FakeTransport):
        def __init__(self, *args):
            super().__init__()
            self.index = 1200

        async def history(self, active, size, count, end):
            return [raw(i) for i in range(self.index + 1) if raw(i)["from"] <= end][-count:]

    p = IQOptionReadOnlyProvider(origin=BASE, transport_factory=Pages)
    try:
        rows = p.bootstrap(META)
        assert len(rows) == 1200
        assert [c.open_time for c in rows] == [BASE + timedelta(minutes=i) for i in range(1200)]
        p._origin = BASE + timedelta(seconds=1)
        with pytest.raises(ValueError, match="IQ_CANONICAL_ORIGIN_UNAVAILABLE"):
            p.bootstrap(META)
    finally:
        p.close()


def test_server_clock_missing_stale_or_disconnected_never_uses_local_time():
    from time import monotonic

    t = IQTransport("unused", "unused")
    socket = _ReadOnlySocket("fake")
    t._client._ws = socket
    for clock, received, dead, error in (
        (None, None, False, "IQ_SERVER_CLOCK_UNAVAILABLE"),
        (Decimal(1), monotonic() - 31, False, "IQ_SERVER_CLOCK_UNAVAILABLE"),
        (Decimal(1), monotonic(), True, "IQ_DISCONNECTED"),
    ):
        socket.server_ms, socket.clock_received, socket.dead = clock, received, dead
        with pytest.raises(IQError, match=error):
            t.server_seconds()


def test_practice_must_exist_not_real_fallback():
    async def scenario():
        t = IQTransport("unused", "unused")

        async def noop():
            pass

        async def response(name, version):
            return [{"id": 1, "type": 1}] if name == "get-balances" else {"id": 1}

        t._client.connect = noop
        t._request = response
        with pytest.raises(IQError, match="IQ_PRACTICE_NOT_VERIFIED"):
            await t.connect()

    asyncio.run(scenario())
