from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import Base
from app.api.deps import db, current_user
from app.models import User, RiskProfile, Trade, LedgerEntry, AuditLog, TradingSession


@pytest.fixture
def desk():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        user = User(email="financial-qa@example.com", name="Financial QA", password_hash="test-only")
        s.add(user)
        s.flush()
        uid = user.id
        s.add(
            RiskProfile(
                user_id=uid,
                risk_per_trade_percent=Decimal("1"),
                max_session_loss_percent=Decimal("2"),
                max_session_operations=4,
                minimum_payout_percent=Decimal("80"),
            )
        )
        s.commit()

    def database():
        with factory() as s:
            yield s

    def actor():
        with factory() as s:
            return s.get(User, uid)

    previous = app.dependency_overrides.copy()
    app.dependency_overrides.update({db: database, current_user: actor})
    with TestClient(app) as client:
        account = client.post("/api/v1/accounts", json={"name": "Review", "initial_balance": "2000"}).json()
        yield client, factory, account["id"]
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)
    engine.dispose()


def start(client, account):
    response = client.post("/api/v1/sessions", json={"trading_account_id": account})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def trade(client, account, sid, stake, result="LOSS"):
    return client.post(
        "/api/v1/trades",
        json={
            "trading_account_id": account,
            "trading_session_id": sid,
            "symbol": "EURUSD",
            "market_type": "REGULAR",
            "timeframe": "1m",
            "direction": "CALL",
            "stake": stake,
            "payout_percent": "84",
            "result": result,
        },
    )


def test_per_trade_boundaries_and_net_session_summary(desk):
    client, factory, account = desk
    sid = start(client, account)
    for stake in ["20.01", "30", "40"]:
        rejected = trade(client, account, sid, stake)
        assert rejected.status_code == 422
        assert rejected.json()["detail"] == "Stake exceeds per-trade risk limit"
    assert trade(client, account, sid, "20.00", "WIN").status_code == 200
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert Decimal(summary["ending_balance"]) == Decimal("2016.80")
    assert Decimal(summary["suggested_stake"]) == Decimal("20.17")
    assert Decimal(summary["loss_consumed"]) == 0
    assert Decimal(summary["remaining_risk"]) == Decimal("40")
    assert trade(client, account, sid, "20.18").status_code == 422
    assert trade(client, account, sid, "20.17").status_code == 200
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    for field, expected in {
        "ending_balance": "1996.63",
        "net_pnl": "-3.37",
        "gross_profit": "16.80",
        "gross_loss": "-20.17",
        "loss_consumed": "3.37",
        "remaining_risk": "36.63",
        "suggested_stake": "19.97",
    }.items():
        assert Decimal(summary[field]) == Decimal(expected), field
    assert not summary["limit_reached"] and summary["limit_reason"] is None
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Trade)) == 2
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 3


def test_session_floor_and_remaining_stake_cap(desk):
    client, _, account = desk
    sid = start(client, account)
    assert trade(client, account, sid, "20").status_code == 200
    assert trade(client, account, sid, "19.80").status_code == 200
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert Decimal(summary["remaining_risk"]) == Decimal(".20")
    assert Decimal(summary["suggested_stake"]) == Decimal(".20")
    assert trade(client, account, sid, ".21").status_code == 422
    assert trade(client, account, sid, ".20").status_code == 200
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert Decimal(summary["net_pnl"]) == Decimal("-40")
    assert Decimal(summary["ending_balance"]) == Decimal("1960")
    assert summary["limit_reached"] and summary["limit_reason"] == "Maximum session loss reached"
    assert trade(client, account, sid, ".01").status_code == 409


@pytest.mark.parametrize("result", ["DRAW", "CANCELLED"])
def test_zero_results_persist_without_ledger_and_count_operations(desk, result):
    client, factory, account = desk
    sid = start(client, account)
    for _ in range(4):
        response = trade(client, account, sid, "20", result)
        assert response.status_code == 200
        assert Decimal(response.json()["profit_loss"]) == 0
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert summary["total_trades"] == 4 and summary["operations_remaining"] == 0
    assert summary["limit_reason"] == "Maximum operations reached"
    assert Decimal(summary["ending_balance"]) == Decimal("2000")
    assert Decimal(summary["loss_consumed"]) == 0 and Decimal(summary["remaining_risk"]) == 40
    assert trade(client, account, sid, "20", result).status_code == 409
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 1
        assert s.scalar(select(func.count()).select_from(Trade)) == 4
        assert s.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.event_type == "TRADE_CREATED")) == 4


def test_missing_profile_and_client_overrides_cannot_create_session(desk):
    client, factory, account = desk
    with factory() as s:
        s.delete(s.scalar(select(RiskProfile)))
        s.commit()
    for path in ["/sessions", f"/accounts/{account}/risk-preview"]:
        response = (
            client.post("/api/v1" + path, json={"trading_account_id": account}) if path == "/sessions" else client.get("/api/v1" + path)
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "No risk profile configured"
    arbitrary = client.post(
        "/api/v1/sessions",
        json={"trading_account_id": account, "risk_per_trade_percent": "100", "max_loss_amount": "2000", "max_operations": 999},
    )
    assert arbitrary.status_code == 422
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(TradingSession)) == 0


def test_snapshot_is_backend_owned_and_frozen(desk):
    client, factory, account = desk
    assert client.post("/api/v1/sessions", json={"trading_account_id": account, "risk_per_trade_percent": "100"}).status_code == 422
    sid = start(client, account)
    with factory() as s:
        profile = s.scalar(select(RiskProfile))
        profile.risk_per_trade_percent = Decimal("5")
        s.commit()
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert Decimal(summary["suggested_stake"]) == 20
    assert trade(client, account, sid, "20.01").status_code == 422
    schema = client.get("/openapi.json").json()["components"]["schemas"]["SessionStartRequest"]
    assert set(schema["properties"]) == {"trading_account_id", "notes"}
