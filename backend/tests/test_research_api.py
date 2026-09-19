from dataclasses import replace
from datetime import timedelta
import pytest
from sqlalchemy import select, func
from app.models import User, BacktestRun, BacktestTrade, AuditLog, StrategyVersion, LedgerEntry
from app.main import app
from app.api.deps import current_user
from app.config import settings
from test_req003 import harness  # noqa: F401
from test_feature_api import seed
from backtest_fixture import candles, config, definition, leaf, BASE


def create(client):
    response = client.post("/api/v1/strategies", json={"name": "Research Example", "description": "Manual regression"})
    assert response.status_code == 200, response.text
    sid = response.json()["id"]
    v = client.post(f"/api/v1/strategies/{sid}/versions", json=definition().model_dump(mode="json"))
    assert v.status_code == 200, v.text
    return sid, v.json()


def execute(client, vid, **kwargs):
    response = client.post("/api/v1/backtests", json=config(strategy_version_id=vid, **kwargs).model_dump(mode="json"))
    assert response.status_code == 200, response.text
    return response.json()


def evidence(client, rid):
    response = client.get(f"/api/v1/backtests/{rid}/trades?limit=100").json()
    return [{k: v for k, v in t.items() if k not in ("id", "backtest_run_id")} for t in response["items"]]


def test_replay_backfill_versions_audit_and_no_real_money(harness):
    client, factory, uid = harness
    seed(factory, candles())
    sid, v1 = create(client)
    a = execute(client, v1["id"])
    assert a["status"] == "COMPLETED" and a["metrics"]["trades_executed"] == 5
    assert a["metrics"]["total_unit_pnl"] == "-0.33"
    assert a["strategy_snapshot"]["definition_sha256"] == v1["definition_sha256"]
    first = evidence(client, a["id"])
    assert first[0]["unit_pnl"] == "0.835" and first[0]["entry_price"] == "105"
    c = candles()[0]
    seed(factory, [replace(c, open_time=BASE - timedelta(minutes=1), close_time=BASE)])
    b = execute(client, v1["id"], as_of_candle_id=a["as_of_candle_id"])
    assert evidence(client, b["id"]) == first and b["metrics"] == a["metrics"]
    assert b["config_sha256"] == a["config_sha256"]
    v2 = client.post(f"/api/v1/strategies/{sid}/versions", json=definition(direction="PUT").model_dump(mode="json")).json()
    assert v2["version"] == 2 and v2["definition_sha256"] != v1["definition_sha256"]
    assert client.get(f"/api/v1/backtests/{a['id']}").json()["strategy_snapshot"] == a["strategy_snapshot"]
    assert client.get("/api/v1/strategies").json()["items"][0]["latest_version"]["version"] == 2
    assert client.get(f"/api/v1/strategies/{sid}/versions?limit=1").json()["total"] == 2
    for path in [f"/api/v1/strategies/{sid}/versions/{v1['id']}", f"/api/v1/backtests/{a['id']}"]:
        assert client.patch(path, json={"result": "WIN"}).status_code in (404, 405)
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(StrategyVersion)) == 2
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 0
        events = list(s.scalars(select(AuditLog.event_type)))
        assert {"STRATEGY_CREATED", "STRATEGY_VERSION_CREATED", "BACKTEST_STARTED", "BACKTEST_COMPLETED"} <= set(events)


@pytest.mark.parametrize("role", ["USER", "ADMIN"])
def test_private_ownership_including_admin(harness, role):
    client, factory, uid = harness
    seed(factory, candles())
    sid, v = create(client)
    run = execute(client, v["id"])
    with factory() as s:
        other = User(email=f"{role}@example.com", name="Other", password_hash="unused", role=role)
        s.add(other)
        s.commit()
        other_id = other.id

    def actor():
        with factory() as s:
            return s.get(User, other_id)

    app.dependency_overrides[current_user] = actor
    for path in [f"/strategies/{sid}", f"/strategies/{sid}/versions", f"/backtests/{run['id']}", f"/backtests/{run['id']}/trades"]:
        assert client.get("/api/v1" + path).status_code == 404
    assert client.post(f"/api/v1/strategies/{sid}/versions", json=definition().model_dump(mode="json")).status_code == 404
    assert client.post("/api/v1/backtests", json=config(strategy_version_id=v["id"]).model_dump(mode="json")).status_code == 404
    assert client.get("/api/v1/strategies").json()["items"] == []
    assert client.get("/api/v1/backtests").json()["items"] == []
    assert client.get("/api/v1/strategies/definitions").status_code == 200


@pytest.mark.parametrize("cap", ["backtest_max_source_candles", "backtest_max_trades"])
def test_caps_failed_run_has_no_partial_evidence(harness, monkeypatch, cap):
    client, factory, _ = harness
    seed(factory, candles())
    _, v = create(client)
    monkeypatch.setattr(settings, cap, 1)
    run = execute(client, v["id"])
    assert run["status"] == "FAILED" and run["metrics"] is None and run["equity_curve"] is None
    assert evidence(client, run["id"]) == []
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(BacktestTrade)) == 0
        assert "BACKTEST_FAILED" in set(s.scalars(select(AuditLog.event_type)))


def test_auth_status_and_invalid_definitions(harness):
    client, _, _ = harness
    sid, v = create(client)
    assert client.patch(f"/api/v1/strategies/{sid}", json={"status": "VALIDATED"}).status_code == 422
    assert client.patch(f"/api/v1/strategies/{sid}", json={"status": "DISABLED"}).status_code == 200
    assert client.post("/api/v1/backtests", json=config(strategy_version_id=v["id"]).model_dump(mode="json")).status_code == 422
    assert (
        client.post(f"/api/v1/strategies/{sid}/versions", json={"trade_direction": "PUT", "condition_tree": leaf("rsi_14")}).status_code
        == 422
    )
    app.dependency_overrides.pop(current_user)
    assert client.get("/api/v1/strategies/definitions").status_code == 401
    assert client.get("/api/v1/backtests").status_code == 401
    assert client.post("/api/v1/backtests", json=config().model_dump(mode="json")).status_code == 401


def test_immutable_orm_evidence_and_atomic_persistence_failure(harness, monkeypatch):
    from sqlalchemy import event

    client, factory, _ = harness
    seed(factory, candles())
    sid, v = create(client)
    run = execute(client, v["id"])
    for model, key, field, value in [(StrategyVersion, v["id"], "trade_direction", "PUT"), (BacktestRun, run["id"], "status", "FAILED")]:
        with factory() as s:
            setattr(s.get(model, key), field, value)
            with pytest.raises(ValueError):
                s.commit()

    def fail(mapper, connection, target):
        raise RuntimeError("injected persistence fault")

    event.listen(BacktestTrade, "before_insert", fail)
    try:
        failed = execute(client, v["id"])
    finally:
        event.remove(BacktestTrade, "before_insert", fail)
    assert failed["status"] == "FAILED" and failed["metrics"] is None
    assert evidence(client, failed["id"]) == []
    assert len(evidence(client, run["id"])) == 5


@pytest.mark.parametrize(
    "field,value", [("source", "OTHER"), ("broker", "OTHER"), ("symbol", "GBPUSD"), ("market_type", "OTC"), ("timeframe", "5m")]
)
def test_backtest_dataset_isolation(harness, field, value):
    client, factory, _ = harness
    data = candles()
    seed(factory, data)
    _, v = create(client)
    a = execute(client, v["id"])
    others = [replace(c, **{field: value}) for c in data]
    seed(factory, others)
    b = execute(client, v["id"])
    assert a["as_of_candle_id"] == b["as_of_candle_id"]
    assert a["metrics"] == b["metrics"] and evidence(client, a["id"]) == evidence(client, b["id"])


def test_bounded_research_request(harness):
    client, _, _ = harness
    assert client.post("/api/v1/strategies", content=b" " * 65537, headers={"Content-Type": "application/json"}).status_code == 413
