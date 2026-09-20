from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import pytest
from sqlalchemy import select, func
from app.models import ScannerWatchItem, ScannerEvent, ScannerOutcome, LiveObservation, Candle, LedgerEntry, User, Strategy, ValidationRun
from app.main import app
from app.api.deps import current_user
from app.live.runtime import ScannerRuntime
from app.live.providers import ReplayLiveProvider, MockLiveProvider, ProviderFrame
from app.config import settings
from test_req003 import harness  # noqa: F401
from test_feature_api import seed
from validation_fixture import create_strategy
from backtest_fixture import candles, BASE, META


def setup(client, factory, normal=False):
    rows = candles([(100, 99), (100, 99), (100, 101), (100, 102), (100, 99), (100, 101)])
    seed(factory, rows)
    sid, vid = create_strategy(client)
    watch = client.post("/api/v1/scanner/watchlists", json={"name": "Private scanner"}).json()
    body = dict(provider="REPLAY", dataset=META, strategy_version_id=vid, research_mode=not normal, research_payout="84", research_expiry=1)
    response = client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json=body)
    return rows, sid, vid, watch, body, response


def test_replay_events_idempotence_paper_and_no_finance(harness):
    client, factory, _ = harness
    rows, _, _, watch, body, response = setup(client, factory)
    assert response.status_code == 200, response.text
    assert client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json=body).status_code == 409
    provider = ReplayLiveProvider(rows, initial=1, payout=Decimal("79"))
    runtime = ScannerRuntime(factory, lambda *args: provider)
    for _ in range(8):
        runtime.cycle()
    events = client.get("/api/v1/scanner/events").json()["items"]
    assert len(events) == 5, events
    assert all(e["mode"] == "REPLAY" for e in events)
    assert sum(e["paper_outcome"] is not None for e in events) == 4
    assert client.get("/api/v1/scanner/items").json()["total"] == 0
    assert client.get("/api/v1/scanner/items?include_research=true").json()["total"] == 1
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Candle)) == 6
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 0
        assert s.scalar(select(func.count()).select_from(LiveObservation)) == 6
        event = s.scalar(select(ScannerEvent))
        event.state = "NO_MATCH"
        with pytest.raises(ValueError):
            s.commit()


def test_forming_duplicate_stale_disconnect_and_conflict(harness):
    client, factory, _ = harness
    rows, *_, response = setup(client, factory)
    iid = response.json()["id"]
    frames = [
        ProviderFrame(rows[1].close_time, forming=rows[1]),
        ProviderFrame(rows[1].close_time, (rows[1],)),
        ProviderFrame(rows[1].close_time, (rows[1],)),
        ProviderFrame(rows[1].close_time + timedelta(minutes=5)),
        ProviderFrame(rows[1].close_time, status="DISCONNECTED"),
    ]
    frames = [replace(frame, mode="REPLAY") for frame in frames]
    runtime = ScannerRuntime(factory, lambda *args: MockLiveProvider(rows[:1], frames))
    runtime.cycle()
    assert client.get("/api/v1/scanner/events").json()["total"] == 0
    runtime.cycle()
    runtime.cycle()
    assert client.get("/api/v1/scanner/events").json()["total"] == 1
    runtime.cycle()
    assert client.get("/api/v1/live/snapshot", params={"item_id": iid}).json()["item"]["state"] == "STALE"
    runtime.cycle()
    assert client.get("/api/v1/live/snapshot", params={"item_id": iid}).json()["item"]["state"] == "PROVIDER_DOWN"
    conflict = replace(rows[1], close=Decimal("98"))
    runtime = ScannerRuntime(
        factory, lambda *args: MockLiveProvider(rows[:1], [ProviderFrame(rows[1].close_time, (conflict,), mode="REPLAY")])
    )
    runtime.cycle()
    assert client.get("/api/v1/live/snapshot", params={"item_id": iid}).json()["item"]["latest"]["error"] == "DATA_CONFLICT"


def test_shared_subscription_bounded_reconnect_no_duplicate_events(harness):
    from app.models import now

    client, factory, _ = harness
    rows, _, _, _, body, response = setup(client, factory)
    watch = client.post("/api/v1/scanner/watchlists", json={"name": "Second watchlist"}).json()
    assert client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json=body).status_code == 200
    calls = []

    def provider(*args):
        calls.append(1)
        if len(calls) == 1:
            return MockLiveProvider(
                rows[:1],
                [
                    ProviderFrame(rows[1].close_time, (rows[1],), payout=Decimal("84"), mode="REPLAY"),
                    ProviderFrame(rows[1].close_time, status="DISCONNECTED", mode="REPLAY"),
                ],
            )
        return ReplayLiveProvider(rows, initial=1, payout=Decimal("84"))

    runtime = ScannerRuntime(factory, provider)
    start = now()
    runtime.cycle(start)
    assert len(calls) == 1 and len(runtime.subscriptions) == 1
    assert client.get("/api/v1/scanner/events").json()["total"] == 2
    runtime.cycle(start + timedelta(seconds=1))
    runtime.cycle(start + timedelta(seconds=2))
    assert len(calls) == 1
    runtime.cycle(start + timedelta(seconds=4))
    assert len(calls) == 2
    assert client.get("/api/v1/scanner/events").json()["total"] == 2
    runtime.cycle(start + timedelta(seconds=5))
    assert client.get("/api/v1/scanner/events").json()["total"] == 4
    assert client.patch(f"/api/v1/scanner/items/{response.json()['id']}", json={"enabled": False}).json()["latest"]["state"] == "PAUSED"


def test_conflict_isolated_from_other_dataset_and_core_modules(harness):
    client, factory, _ = harness
    rows, _, _, watch, body, response = setup(client, factory)
    other_meta = {**META, "broker": "OTHER"}
    other = client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json={**body, "dataset": other_meta})
    assert other.status_code == 200
    good_rows = [replace(c, broker="OTHER") for c in rows]
    bad = MockLiveProvider(rows[:1], [ProviderFrame(rows[1].close_time, (replace(rows[1], close=Decimal("98")),), mode="REPLAY")])
    good = MockLiveProvider(good_rows[:1], [ProviderFrame(c.close_time, (c,), mode="REPLAY") for c in good_rows[1:3]])
    runtime = ScannerRuntime(factory, lambda s, p, d: good if d.broker == "OTHER" else bad)
    runtime.cycle()
    runtime.cycle()
    items = {x["id"]: x for x in client.get("/api/v1/scanner/items?include_research=true").json()["items"]}
    assert items[response.json()["id"]]["latest"]["error"] == "DATA_CONFLICT"
    assert items[other.json()["id"]]["state"] == "ACTIVE"
    events = client.get("/api/v1/scanner/events").json()["items"]
    assert len(events) == 2 and all(e["dataset"]["broker"] == "OTHER" for e in events)
    assert client.get("/api/v1/accounts").status_code == 200
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    runtime.close()


@pytest.mark.parametrize("role", ["USER", "ADMIN"])
def test_ownership_and_validation_compatibility(harness, role):
    client, factory, _ = harness
    _, _, vid, watch, body, response = setup(client, factory)
    assert client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json={**body, "research_mode": False}).status_code == 422
    assert (
        client.post(
            f"/api/v1/scanner/watchlists/{watch['id']}/items", json={**body, "provider": "MT5", "dataset": {**META, "market_type": "OTC"}}
        ).status_code
        == 422
    )
    with factory() as s:
        other = User(name="Other", email="scanner-other@example.com", password_hash="unused", role=role)
        s.add(other)
        s.commit()
        oid = other.id

    def actor():
        with factory() as s:
            return s.get(User, oid)

    app.dependency_overrides[current_user] = actor
    assert client.get("/api/v1/scanner/watchlists").json()["total"] == 0
    assert client.get("/api/v1/scanner/events").json()["total"] == 0
    assert client.get("/api/v1/live/snapshot", params={"item_id": response.json()["id"]}).status_code == 404
    assert client.patch(f"/api/v1/scanner/items/{response.json()['id']}", json={"enabled": False}).status_code == 404


def test_provider_flags_and_heartbeat(harness, monkeypatch):
    client, factory, _ = harness
    _, _, _, _, _, response = setup(client, factory)
    monkeypatch.setattr(settings, "enable_mt5_provider", False)
    assert next(p for p in client.get("/api/v1/live/providers").json()["items"] if p["provider"] == "MT5")["enabled"] is False
    with factory() as s:
        item = s.get(ScannerWatchItem, response.json()["id"])
        item.updated_at = BASE
        s.commit()
    assert client.get("/api/v1/live/snapshot", params={"item_id": response.json()["id"]}).json()["item"]["state"] == "PROVIDER_DOWN"


def test_real_validation_payout_dataset_isolation_and_degraded_suspension(harness):
    from validation_fixture import data
    from test_validation_api import create

    client, factory, _ = harness
    rows = data()
    later = [
        replace(c, open_time=c.open_time + timedelta(hours=1500), close_time=c.close_time + timedelta(hours=1500))
        for c in data(losing_test=True)
    ]
    seed(factory, rows + later)
    _, vid = create_strategy(client)
    plan = create(client, vid)
    assert client.post(f"/api/v1/validations/{plan['id']}/reveal-test").json()["verdict"] == "PASS"
    watch = client.post("/api/v1/scanner/watchlists", json={"name": "Validated"}).json()
    body = dict(provider="REPLAY", dataset={**META, "timeframe": "1h"}, strategy_version_id=vid)
    for field, value in [("source", "OTHER"), ("broker", "OTHER"), ("symbol", "GBPUSD"), ("market_type", "OTC"), ("timeframe", "1m")]:
        assert (
            client.post(
                f"/api/v1/scanner/watchlists/{watch['id']}/items", json={**body, "dataset": {**body["dataset"], field: value}}
            ).status_code
            == 422
        )
    item = client.post(f"/api/v1/scanner/watchlists/{watch['id']}/items", json=body)
    assert item.status_code == 200, item.text
    runtime = ScannerRuntime(factory, lambda *args: ReplayLiveProvider(rows, initial=1490, payout=Decimal("79")))
    runtime.cycle()
    event = client.get("/api/v1/scanner/events").json()["items"][0]
    assert event["evidence"]["payout_warning"] is True
    assert Decimal(event["evidence"]["validation_payout"]) == Decimal("83.5")
    assert Decimal(event["current_payout"]) == 79
    plan = create(client, vid, overall_start=BASE + timedelta(hours=1500), overall_end=BASE + timedelta(hours=3000))
    assert client.post(f"/api/v1/validations/{plan['id']}/reveal-test").json()["validation_state"] == "DEGRADED"
    runtime.cycle()
    assert client.get("/api/v1/scanner/items").json()["items"][0]["state"] == "SUSPENDED_DEGRADED"
    assert client.get("/api/v1/scanner/events").json()["total"] == 1


@pytest.mark.parametrize(
    "research,provider,payout,source,expiry,expiry_source",
    [
        (True, None, "90", "RESEARCH_ASSUMPTION", 3, "RESEARCH_ASSUMPTION"),
        (True, "87", "87", "PROVIDER", 3, "RESEARCH_ASSUMPTION"),
        (False, None, "84", "VALIDATION_ASSUMPTION", 1, "VALIDATION_ASSUMPTION"),
        (False, "79", "79", "PROVIDER", 1, "VALIDATION_ASSUMPTION"),
    ],
)
def test_paper_precedence_with_real_validation_and_observed_outcome(harness, research, provider, payout, source, expiry, expiry_source):
    from validation_fixture import data
    from test_validation_api import create

    client, factory, _ = harness
    rows = data()
    seed(factory, rows)
    _, vid = create_strategy(client)
    plan = create(client, vid, payout_percent="84")
    assert client.post(f"/api/v1/validations/{plan['id']}/reveal-test").json()["verdict"] == "PASS"
    watch = client.post("/api/v1/scanner/watchlists", json={"name": "Precedence"}).json()
    response = client.post(
        f"/api/v1/scanner/watchlists/{watch['id']}/items",
        json=dict(
            provider="REPLAY",
            dataset={**META, "timeframe": "1h"},
            strategy_version_id=vid,
            research_mode=research,
            research_payout="90",
            research_expiry=3,
        ),
    )
    assert response.status_code == 200, response.text
    replay = ReplayLiveProvider(rows, initial=1490, payout=Decimal(provider) if provider else None)
    if provider is None:
        replay.capabilities["payout"] = False
    runtime = ScannerRuntime(factory, lambda *args: replay)
    runtime.cycle()
    first = client.get("/api/v1/scanner/events").json()["items"][0]
    evidence = first["evidence"]
    assert Decimal(evidence["payout_snapshot"]) == Decimal(payout)
    assert evidence["payout_source"] == source
    assert (evidence["expiry_bars"], evidence["expiry_source"]) == (expiry, expiry_source)
    assert Decimal(evidence["validation_payout"]) == 84 and evidence["validation_expiry"] == 1
    assert evidence["payout_warning"] == (provider == "79")
    assert first["paper_outcome"] is None
    for i in range(expiry):
        runtime.cycle()
        event = next(e for e in client.get("/api/v1/scanner/events").json()["items"] if e["id"] == first["id"])
        if i < expiry - 1:
            assert event["paper_outcome"] is None
    paper = event["paper_outcome"]["evidence"]
    assert paper["result"] == "WIN"
    assert Decimal(paper["entry_price"]) == rows[1491].open
    assert paper["entry_time"] == rows[1491].open_time.isoformat()
    assert paper["expiry_time"] == rows[1490 + expiry].close_time.isoformat()
    assert Decimal(paper["unit_pnl"]) == Decimal(payout) / 100
    assert paper["payout_source"] == source
