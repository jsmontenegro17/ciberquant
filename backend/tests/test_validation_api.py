from dataclasses import replace
from datetime import timedelta
import pytest
from sqlalchemy import select, func, event
from app.models import ValidationRun, ValidationSegment, BacktestRun, BacktestTrade, User, AuditLog
from app.main import app
from app.api.deps import current_user
from test_req003 import harness  # noqa: F401
from test_feature_api import seed
from validation_fixture import data, request, create_strategy, BASE


def create(client, vid, size=1500, **kwargs):
    response = client.post("/api/v1/validations", json=request(size, strategy_version_id=vid, **kwargs).model_dump(mode="json"))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "SEALED", response.text
    return response.json()


@pytest.mark.parametrize("size,losing,expected", [(1500, False, "PASS"), (1500, True, "FAIL"), (100, False, "INCONCLUSIVE")])
def test_sealed_explicit_reveal_verdict_and_evidence(harness, size, losing, expected):
    client, factory, _ = harness
    seed(factory, data(size, losing))
    sid, vid = create_strategy(client)
    plan = create(client, vid, size)
    rid = plan["id"]
    assert plan["verdict"] == "PENDING_TEST"
    assert plan["test_summary"] is None and plan["bootstrap_summary"] is None
    assert len(plan["walk_forward_summary"]) == 4
    assert client.get("/api/v1/backtests").json()["total"] == 0
    segments = client.get(f"/api/v1/validations/{rid}/segments").json()
    assert len(segments) == 7 and next(s for s in segments if s["segment_type"] == "TEST")["backtest_run_id"] is None
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(BacktestRun)) == 6
        assert s.scalar(select(func.max(BacktestTrade.expiry_candle_id))) <= size * 4 // 5
    final = client.post(f"/api/v1/validations/{rid}/reveal-test").json()
    assert final["status"] == "COMPLETED", final
    assert final["verdict"] == expected
    assert final["validation_state"] == ("HISTORICALLY_VALIDATED" if expected == "PASS" else "NOT_VALIDATED")
    assert final["test_revealed_at"] and len(final["gates"]) == 8
    assert client.post(f"/api/v1/validations/{rid}/reveal-test").status_code == 409
    with factory() as s:
        events = set(s.scalars(select(AuditLog.event_type)))
        assert {"VALIDATION_STARTED", "VALIDATION_DEVELOPMENT_COMPLETED", "VALIDATION_TEST_REVEALED", "VALIDATION_COMPLETED"} <= events
    for model, key, field, value in [
        (ValidationRun, rid, "verdict", "FAIL"),
        (ValidationSegment, segments[0]["id"], "backtest_run_id", 999),
    ]:
        with factory() as s:
            setattr(s.get(model, key), field, value if expected != "FAIL" else "PASS" if field == "verdict" else value)
            with pytest.raises(ValueError):
                s.commit()


def test_snapshot_replay_backfill_holdout_and_preview(harness):
    client, factory, _ = harness
    rows = data(100)
    seed(factory, rows)
    _, vid = create_strategy(client)
    preview = client.post("/api/v1/validations/preview", json=request(100, strategy_version_id=vid).model_dump(mode="json")).json()
    first = create(client, vid, 100)
    assert preview["config_sha256"] == first["config_sha256"]
    a = client.post(f"/api/v1/validations/{first['id']}/reveal-test").json()
    seed(factory, [replace(rows[0], open_time=BASE - timedelta(hours=1), close_time=BASE)])
    replay = create(client, vid, 100, as_of_candle_id=first["as_of_candle_id"])
    assert replay["config_sha256"] == first["config_sha256"]
    assert replay["holdout_warnings"] == dict(
        prior_validation_count=1, prior_revealed_holdout_count=1, overlapping_holdout_count=1, replay_count=1
    )
    b = client.post(f"/api/v1/validations/{replay['id']}/reveal-test").json()
    for k in ["development_summary", "walk_forward_summary", "test_summary", "bootstrap_summary", "temporal_stability", "gates", "verdict"]:
        assert a[k] == b[k]


@pytest.mark.parametrize("role", ["USER", "ADMIN"])
def test_ownership_status_and_no_mutation(harness, role):
    client, factory, _ = harness
    seed(factory, data(100))
    sid, vid = create_strategy(client)
    run = create(client, vid, 100)
    for status in ["DRAFT", "DISABLED"]:
        client.patch(f"/api/v1/strategies/{sid}", json={"status": status})
        assert client.post("/api/v1/validations", json=request(100, strategy_version_id=vid).model_dump(mode="json")).status_code == 422
    with factory() as s:
        other = User(name="Other", email="validation-other@example.com", role=role, password_hash="unused")
        s.add(other)
        s.commit()
        oid = other.id

    def actor():
        with factory() as s:
            return s.get(User, oid)

    app.dependency_overrides[current_user] = actor
    assert client.get("/api/v1/validations").json()["total"] == 0
    for path in [f"/validations/{run['id']}", f"/validations/{run['id']}/segments"]:
        assert client.get("/api/v1" + path).status_code == 404
    assert client.post(f"/api/v1/validations/{run['id']}/reveal-test").status_code == 404
    assert client.post("/api/v1/validations", json=request(100, strategy_version_id=vid).model_dump(mode="json")).status_code == 404


def test_phase_failure_atomic_and_unrepeatable_reveal(harness):
    client, factory, _ = harness
    seed(factory, data(100))
    _, vid = create_strategy(client)
    run = create(client, vid, 100)

    def injected(*args):
        raise RuntimeError("injected")

    event.listen(BacktestTrade, "before_insert", injected)
    try:
        failure = client.post(f"/api/v1/validations/{run['id']}/reveal-test").json()
    finally:
        event.remove(BacktestTrade, "before_insert", injected)
    assert failure["status"] == "FAILED" and failure["test_summary"] is None
    assert failure["test_revealed_at"] is not None
    assert client.post(f"/api/v1/validations/{run['id']}/reveal-test").status_code == 409
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(BacktestRun)) == 6


def test_sealing_never_computes_test_rows_and_refreshes_reuse_at_reveal(harness, monkeypatch):
    from app.validation import repository

    client, factory, _ = harness
    seed(factory, data(100))
    _, vid = create_strategy(client)
    computed = []
    original = repository.compute

    def spy(candles, specs):
        rows = list(candles)
        computed.append(max(c.open_time for c in rows))
        return original(rows, specs)

    monkeypatch.setattr(repository, "compute", spy)
    a, b = create(client, vid, 100), create(client, vid, 100)
    assert len(computed) == 2 and max(computed) == BASE + timedelta(hours=79)
    client.post(f"/api/v1/validations/{a['id']}/reveal-test")
    result = client.post(f"/api/v1/validations/{b['id']}/reveal-test").json()
    assert result["holdout_warnings"]["overlapping_holdout_count"] == 1
    assert max(computed) == BASE + timedelta(hours=99)


def test_real_persisted_pass_then_later_fail_degrades(harness):
    client, factory, _ = harness
    seed(factory, data())
    seed(
        factory,
        [
            replace(c, open_time=c.open_time + timedelta(hours=1500), close_time=c.close_time + timedelta(hours=1500))
            for c in data(losing_test=True)
        ],
    )
    _, vid = create_strategy(client)
    first = create(client, vid)
    assert client.post(f"/api/v1/validations/{first['id']}/reveal-test").json()["validation_state"] == "HISTORICALLY_VALIDATED"
    later = create(client, vid, overall_start=BASE + timedelta(hours=1500), overall_end=BASE + timedelta(hours=3000))
    result = client.post(f"/api/v1/validations/{later['id']}/reveal-test").json()
    assert result["verdict"] == "FAIL" and result["validation_state"] == "DEGRADED"


def test_plan_immutable_while_sealed_and_body_constraints(harness):
    client, factory, _ = harness
    seed(factory, data(100))
    _, vid = create_strategy(client)
    run = create(client, vid, 100)
    with factory() as s:
        r = s.get(ValidationRun, run["id"])
        r.payout_percent = 90
        with pytest.raises(ValueError):
            s.commit()
    body = request(100, strategy_version_id=vid).model_dump(mode="json")
    for field, value in [
        ("split", [50, 25, 25]),
        ("verdict", "PASS"),
        ("expiry_bars", 0),
        ("payout_percent", 84),
        ("as_of_candle_id", 999999),
    ]:
        assert client.post("/api/v1/validations", json={**body, field: value}).status_code == 422
    assert client.post("/api/v1/validations", content=b" " * 65537).status_code == 413


def test_changed_payout_or_expiry_requires_new_version(harness):
    from backtest_fixture import definition

    client, factory, _ = harness
    seed(factory, data(100))
    sid, vid = create_strategy(client)
    create(client, vid, 100)
    body = request(100, strategy_version_id=vid).model_dump(mode="json")
    for field, value in [("payout_percent", "84"), ("expiry_bars", 2)]:
        for path in ["/validations", "/validations/preview"]:
            response = client.post("/api/v1" + path, json={**body, field: value})
            assert response.status_code == 422
            assert "new StrategyVersion" in response.json()["detail"]
    version = client.post(f"/api/v1/strategies/{sid}/versions", json=definition().model_dump(mode="json")).json()
    create(client, version["id"], 100, payout_percent="84", expiry_bars=2)
