from app.models import User, LedgerEntry
from app.main import app
from app.api.deps import current_user
from sqlalchemy import select, func
from test_req003 import harness  # noqa: F401
from test_scanner_api import setup
from backtest_fixture import META


def test_exact_context_missing_stages_and_no_side_effects(harness):
    client, factory, _ = harness
    _, _, vid, *_ = setup(client, factory)
    params = dict(**META, strategy_version_id=vid)
    response = client.get("/api/v1/workspace/overview", params=params)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dataset"] == META
    assert body["version"]["id"] == vid
    stages = {s["name"]: s for s in body["pipeline"]}
    assert stages["DATA"]["status"] == "READY"
    assert stages["BACKTEST"]["status"] == "MISSING"
    assert stages["PAPER"]["status"] == "MISSING"
    assert body["journal"]["association"] == "NONE"
    for key, value in [("source", "OTHER"), ("broker", "OTHER"), ("symbol", "OTHER"), ("market_type", "OTC"), ("timeframe", "5m")]:
        other = client.get("/api/v1/workspace/overview", params={**params, key: value}).json()
        assert other["pipeline"][0]["status"] == "MISSING"
        assert other["provider_health"] == []
    for path in ("events", "paper", "history"):
        q = client.get("/api/v1/workspace/" + path, params={**params, "kind": "manual"})
        assert q.status_code == 200, q.text
        assert q.json()["total"] == 0
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_workspace_cross_user_and_missing_version(harness):
    client, factory, _ = harness
    _, _, vid, *_ = setup(client, factory)
    with factory() as s:
        other = User(email="workspace-other@example.invalid", name="Other", password_hash="unused")
        s.add(other)
        s.commit()
        s.refresh(other)
        s.expunge(other)
    app.dependency_overrides[current_user] = lambda: other
    for path in ("overview", "events", "paper", "history", "comparison"):
        r = client.get(
            "/api/v1/workspace/" + path, params={**META, "strategy_version_id": vid, "kind": "manual", "backtest_id": 1, "validation_id": 1}
        )
        assert r.status_code == 404, r.text
    assert client.get("/api/v1/workspace/events/99999").status_code == 404


def test_manual_validation_lineage_comparison_and_paper(harness):
    from test_feature_api import seed
    from validation_fixture import data, request, create_strategy
    from app.backtesting.schemas import RunCreate
    from app.backtesting.repository import run_backtest
    from app.validation.repository import create, reveal
    from app.live.runtime import ScannerRuntime
    from app.live.providers import ReplayLiveProvider
    from decimal import Decimal

    client, factory, uid = harness
    rows = data(100)
    seed(factory, rows)
    sid, vid = create_strategy(client)
    req = request(100, strategy_version_id=vid)
    with factory() as s:
        manual = run_backtest(
            s,
            uid,
            RunCreate(
                strategy_version_id=vid,
                dataset=req.dataset,
                signal_start=req.overall_start,
                signal_end=req.overall_end,
                payout_percent="83.5",
                expiry_bars=1,
            ),
        )
        mid = manual.id
        validation = create(s, uid, req)
        validation = reveal(s, uid, validation.id)
        rid = validation.id
    summary = client.get("/api/v1/strategies").json()["items"][0]
    assert summary["last_backtest"]["id"] == mid
    assert summary["latest_validation"]["id"] == rid
    params = {**req.dataset.model_dump(), "strategy_version_id": vid}
    comparison = client.get("/api/v1/workspace/comparison", params={**params, "backtest_id": mid, "validation_id": rid}).json()
    assert comparison["status"] == "CONTEXT_ALIGNED_NOT_POOLED"
    assert len(comparison["validation_children"]) == 7
    mismatch = client.get(
        "/api/v1/workspace/comparison", params={**params, "broker": "OTHER", "backtest_id": mid, "validation_id": rid}
    ).json()
    assert mismatch["status"] == "INCOMPATIBLE" and "manual: dataset.broker" in mismatch["differences"]
    child = comparison["validation_children"][0]["backtest_run_id"]
    mismatch = client.get("/api/v1/workspace/comparison", params={**params, "backtest_id": child, "validation_id": rid}).json()
    assert "validation child is not a manual backtest" in mismatch["differences"]
    watch = client.post("/api/v1/scanner/watchlists", json={"name": "Workspace evidence"}).json()
    item = client.post(
        f"/api/v1/scanner/watchlists/{watch['id']}/items",
        json={
            "provider": "REPLAY",
            "dataset": req.dataset.model_dump(),
            "strategy_version_id": vid,
            "research_mode": True,
            "research_payout": "84",
            "research_expiry": 1,
        },
    )
    assert item.status_code == 200, item.text
    runtime = ScannerRuntime(factory, lambda *args: ReplayLiveProvider(rows, initial=95, payout=Decimal("79")))
    for _ in range(7):
        runtime.cycle()
    runtime.close()
    events = client.get("/api/v1/workspace/events", params={**params, "limit": 1}).json()
    assert events["total"] == 5 and len(events["items"]) == 1
    detail = client.get("/api/v1/workspace/events/" + str(events["items"][0]["id"])).json()
    assert detail["event"]["strategy_version_id"] == vid
    assert detail["live_provenance"] and detail["candle_id"]
    paper = client.get("/api/v1/workspace/paper", params=params).json()
    assert paper["total"] > 0 and all(r["mode"] == "REPLAY" for r in paper["items"])
    assert all(r["payout_source"] == "PROVIDER" for r in paper["items"])
    assert client.get("/api/v1/operations/status").status_code == 200


def test_stale_health_and_query_bound(harness):
    from app.models import WorkerHeartbeat, LiveSubscription, ScannerWatchItem, now
    from datetime import timedelta
    from sqlalchemy import event

    client, factory, _ = harness
    _, _, vid, *_ = setup(client, factory)
    with factory() as s:
        item = s.scalar(select(ScannerWatchItem))
        s.add(
            LiveSubscription(
                key=item.subscription_key,
                provider="REPLAY",
                dataset=META,
                status="CONNECTED",
                health={},
                updated_at=now() - timedelta(minutes=10),
            )
        )
        s.add(WorkerHeartbeat(name="scanner", status="RUNNING", updated_at=now() - timedelta(minutes=10)))
        s.commit()
    calls = []
    engine = factory.kw["bind"]

    def counted(*args):
        calls.append(args[2])

    event.listen(engine, "before_cursor_execute", counted)
    try:
        result = client.get("/api/v1/workspace/overview", params={**META, "strategy_version_id": vid}).json()
    finally:
        event.remove(engine, "before_cursor_execute", counted)
    assert len(calls) <= 12
    assert result["provider_health"][0]["status"] == "STALE"
    assert client.get("/api/v1/operations/status").json()["worker"]["state"] == "STALE"
