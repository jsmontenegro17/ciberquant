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
from test_req003 import harness  # noqa: F401

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
        assert p.status_metadata["finality_policy"] == "FAIL_CLOSED_ON_REVISION"
        assert p.status_metadata["immutable_finality"] == "NOT_GUARANTEED"
        assert p.status_metadata["balance_mode"] == "PRACTICE" and p.status_metadata["read_only"] is True
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


def test_history_tracker_revisions_exact_identity_and_safe_projection():
    from scripts.iq_diagnostics import HistoryTracker

    emitted = []
    tracker = HistoryTracker(emitted.append)
    fake = FakeTransport()
    p = IQOptionReadOnlyProvider(origin=BASE, transport_factory=lambda *args: fake, history_observer=tracker.observe)
    try:
        p.bootstrap(META)
        p.poll(META)
        assert tracker.conflicts == []
        original = fake.history

        async def revised(*args):
            rows = await original(*args)
            rows[1]["close"] = "1.10003"
            return rows

        fake.history = revised
        p.poll(META)
        assert tracker.conflicts[0]["changed_fields"] == ["close"]
        assert tracker.conflicts[0]["revised"]["active_id"] == 42
        assert tracker.conflicts[0]["revised"]["history_request_count"] == 3
        assert tracker.conflicts[0]["revised"]["ohlc"]["close"] == "1.10003"
        assert all("password" not in json.dumps(e, default=str) for e in emitted)
        other = META.model_copy(update={"broker": "OTHER"})
        tracker.observe(other, [normalize_candle(raw(1), other, 42)], {"provider_time": BASE + timedelta(minutes=3)})
        assert len(tracker.conflicts) == 1
        from dataclasses import replace

        same = replace(normalize_candle(raw(1), other, 42), close=Decimal("1.1000200000"))
        tracker.observe(other, [same], {"provider_time": BASE + timedelta(minutes=3)})
        assert len(tracker.conflicts) == 1  # Decimal equality, not display-scale equality.
    finally:
        p.close()


def test_numeric_limit_rejects_rounding_and_exact_json_decimal():
    from app.market_data.quality import validate_candle
    from dataclasses import replace

    candle = normalize_candle(raw(), META, 42)
    assert validate_candle(replace(candle, close=Decimal("1.10002000001")))
    assert not validate_candle(replace(candle, close=Decimal("1.1000200000")))
    for field in ("open", "high", "low", "close"):
        assert isinstance(getattr(candle, field), Decimal)


def test_fake_transport_revision_fails_closed_without_overwrite(harness):
    from sqlalchemy import select, func
    from app.models import Strategy, User, ScannerWatchlist, ScannerWatchItem, ScannerEvent, Candle, LiveSubscription
    from app.strategies.repository import create_version
    from app.strategies.schemas import VersionCreate
    from app.strategies.dsl import digest
    from app.live.runtime import ScannerRuntime
    from app.live.conflicts import DataConflictError

    client, factory, _ = harness
    fake = FakeTransport()
    p = IQOptionReadOnlyProvider(origin=BASE, transport_factory=lambda *a: fake)
    key = digest(dict(provider="IQOPTION", dataset=META.model_dump()))
    with factory() as s:
        user = s.scalar(select(User))
        strategy = Strategy(user_id=user.id, name="revision diagnostic", status="TESTING")
        s.add(strategy)
        s.commit()
        version = create_version(
            s,
            strategy.id,
            user.id,
            VersionCreate(
                trade_direction="CALL",
                indicator_specs=[],
                condition_tree={
                    "left": {"type": "FIELD", "field": "close", "bars_ago": 0},
                    "operator": "GT",
                    "right": {"type": "NUMBER", "value": "0"},
                },
            ),
        )
        watch = ScannerWatchlist(user_id=user.id, name="revision")
        s.add(watch)
        s.flush()
        s.add(
            ScannerWatchItem(
                user_id=user.id,
                watchlist_id=watch.id,
                strategy_version_id=version.id,
                provider="IQOPTION",
                dataset=META.model_dump(),
                subscription_key=key,
                research_mode=True,
                research_payout=Decimal(84),
                research_expiry=1,
            )
        )
        s.commit()
        version_id = version.id
    captured = []

    def sink(exc):
        captured.append(exc)
        raise RuntimeError("Synthetic diagnostic writer failure")

    runtime = ScannerRuntime(factory, lambda *a: p, diagnostic_sink=sink)
    try:
        runtime.cycle(BASE + timedelta(minutes=2, seconds=10))
        fake.index = 3
        runtime.cycle(BASE + timedelta(minutes=3, seconds=10))
        state_before_conflict = runtime.subscriptions[key]
        history_size = len(state_before_conflict.history)
        feature_sizes = {vid: len(state.rows) for vid, (state, _) in state_before_conflict.features.items()}
        with factory() as s:
            assert s.scalar(select(func.count()).select_from(ScannerEvent)) == 1
            before = s.scalar(select(Candle).where(Candle.open_time == BASE + timedelta(minutes=2))).close
        original = fake.history

        async def revised(*args):
            rows = await original(*args)
            rows[2]["close"] = "1.10003"
            return rows

        fake.history = revised
        runtime.cycle(BASE + timedelta(minutes=3, seconds=11))
        assert len(captured) == 1 and isinstance(captured[0], DataConflictError)
        assert isinstance(captured[0], ValueError) and str(captured[0]) == "DATA_CONFLICT"
        assert captured[0].details["detection_layer"] == "RUNTIME_OBSERVED_PERSISTENCE"
        assert captured[0].details["old_close"] == str(before)
        assert captured[0].details["new_close"] == "1.10003"
        assert p._closed and runtime.retry[key][2] is True
        assert len(state_before_conflict.history) == history_size
        assert {vid: len(state.rows) for vid, (state, _) in state_before_conflict.features.items()} == feature_sizes
        runtime.cycle(BASE + timedelta(minutes=5))
        attempts = []
        restarted = ScannerRuntime(factory, lambda *args: attempts.append(args))
        restarted.cycle(BASE + timedelta(minutes=6))
        restarted.cycle(BASE + timedelta(minutes=7))
        assert attempts == []  # Persisted conflict survives process restart: no reconnect attempt.
        assert restarted.retry[key][2] is True
        with factory() as s:
            assert s.scalar(select(func.count()).select_from(ScannerEvent)) == 1
            assert s.scalar(select(Candle).where(Candle.open_time == BASE + timedelta(minutes=2))).close == before
            assert s.get(LiveSubscription, key).health["error"] == "DATA_CONFLICT"
            iid = s.scalar(select(ScannerWatchItem.id))
        snapshot = client.get("/api/v1/live/snapshot", params={"item_id": iid}).json()
        assert snapshot["item"]["latest"]["error"] == "DATA_CONFLICT"
        assert snapshot["subscription"]["health"]["error"] == "DATA_CONFLICT"
        overview = client.get("/api/v1/workspace/overview", params={**META.model_dump(), "strategy_version_id": version_id}).json()
        assert next(stage for stage in overview["pipeline"] if stage["name"] == "SCANNER")["status"] == "FAILED"
    finally:
        runtime.close()
        p.close()


def test_bootstrap_conflict_diagnostics_preserve_first_observation(harness):
    from app.live.conflicts import DataConflictError
    from app.live.persistence import persist_closed
    from dataclasses import replace
    from sqlalchemy import select, func
    from app.models import Candle

    _, factory, _ = harness
    original = normalize_candle(raw(), META, 42)
    revised = replace(original, close=Decimal("1.10003"))
    with factory() as s:
        persist_closed(s, META, [original], "IQOPTION", "LIVE", BASE + timedelta(minutes=1), BASE + timedelta(minutes=1), "BOOTSTRAP")
        s.commit()
    with factory() as s:
        with pytest.raises(DataConflictError) as caught:
            persist_closed(s, META, [revised], "IQOPTION", "LIVE", BASE + timedelta(minutes=2), BASE + timedelta(minutes=2), "BOOTSTRAP")
        assert str(caught.value) == "DATA_CONFLICT"
        assert caught.value.details["detection_layer"] == "RUNTIME_BOOTSTRAP_PERSISTENCE"
        assert caught.value.details["age_after_close_first_ms"] is None
        assert caught.value.details["age_after_close_second_ms"] is None
        assert caught.value.details["first_persisted_clock_source"] == "LOCAL_BOOTSTRAP_RECEIVE"
        s.rollback()
        assert s.scalar(select(func.count()).select_from(Candle)) == 1
        assert s.scalar(select(Candle)).close == original.close


def test_repeated_bootstrap_and_poll_do_not_change_request_identity():
    fake = FakeTransport()
    requests = []
    original = fake.history

    async def capture(active, size, count, end):
        requests.append((active, size, count, end))
        return await original(active, size, count, end)

    fake.history = capture
    p = IQOptionReadOnlyProvider(origin=BASE, transport_factory=lambda *a: fake)
    try:
        a = p.bootstrap(META)
        b = p.bootstrap(META)
        frame = p.poll(META)
        assert a == b and frame.closed[-1] == a[-1]
        assert requests[0] == requests[1]
        assert {r[:2] for r in requests} == {(42, 60)}
        assert [r[2] for r in requests] == [1000, 1000, 3]
    finally:
        p.close()
