from decimal import Decimal
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.main import app
from app.api.deps import db
from app.models import User, TradingAccount, TradingSession, Trade, LedgerEntry, AuditLog, RiskProfile


def test_req002_complete_workflow_and_isolation():
    setup_user("workflow@example.com")
    login("workflow@example.com")
    account = client.post("/api/v1/accounts", json={"name": "Workflow", "initial_balance": "2000"}).json()
    other_account = client.post("/api/v1/accounts", json={"name": "Other", "initial_balance": "500"}).json()
    with TestingSession() as s:
        user = s.scalar(select(User).where(User.email == "workflow@example.com"))
        s.add(
            RiskProfile(
                user_id=user.id,
                risk_per_trade_percent=Decimal("1"),
                max_session_loss_percent=Decimal("2"),
                max_session_operations=2,
                minimum_payout_percent=Decimal("80"),
            )
        )
        s.commit()
    preview = client.get(f"/api/v1/accounts/{account['id']}/risk-preview").json()
    assert Decimal(preview["suggested_stake"]) == Decimal("20")
    session = client.post("/api/v1/sessions", json={"trading_account_id": account["id"]}).json()
    sid = session["id"]
    assert client.post("/api/v1/sessions", json={"trading_account_id": account["id"]}).status_code == 409
    body = {
        "trading_account_id": account["id"],
        "trading_session_id": sid,
        "symbol": "EURUSD",
        "market_type": "REGULAR",
        "timeframe": "1m",
        "direction": "CALL",
        "stake": "20",
        "payout_percent": "84",
        "result": "WIN",
    }
    assert client.post("/api/v1/trades", json={**body, "trading_account_id": other_account["id"]}).status_code == 422
    assert client.post("/api/v1/trades", json={**body, "payout_percent": "79"}).status_code == 422
    win = client.post("/api/v1/trades", json=body)
    assert win.status_code == 200
    assert Decimal(win.json()["profit_loss"]) == Decimal("16.80")
    second = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert Decimal(second["ending_balance"]) == Decimal("2016.80")
    assert Decimal(second["suggested_stake"]) == Decimal("20.17")
    loss = client.post("/api/v1/trades", json={**body, "stake": second["suggested_stake"], "result": "LOSS"})
    assert loss.status_code == 200
    assert client.post("/api/v1/trades", json=body).status_code == 409
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert summary["limit_reached"] and summary["operations_remaining"] == 0
    assert summary["wins"] == summary["losses"] == 1
    assert Decimal(summary["net_pnl"]) == Decimal("-3.37")
    assert Decimal(summary["win_rate"]) == Decimal("50")
    note = client.post("/api/v1/journal", json={"title": "Review", "content": "Observed patiently", "trade_id": win.json()["id"]})
    assert note.status_code == 200 and note.json()["session_id"] == sid
    assert client.get("/api/v1/journal").json()[0]["content"] == "Observed patiently"
    closed = client.post(f"/api/v1/sessions/{sid}/close").json()
    assert closed["status"] == "CLOSED" and closed["ended_at"]
    assert Decimal(closed["ending_balance"]) == Decimal("1996.63")
    ledger = client.get(f"/api/v1/accounts/{account['id']}/ledger").json()
    assert len(ledger) == 3 and Decimal(ledger[0]["balance_after"]) == Decimal("1996.63")
    overview = client.get(f"/api/v1/analytics/overview?account_id={account['id']}").json()
    assert overview["max_win_streak"] == overview["max_loss_streak"] == 1
    assert Decimal(overview["month_pnl"]) == Decimal("-3.37") and overview["current_session"] is None
    setup_user("intruder@example.com")
    login("intruder@example.com")
    for path in [
        f"/sessions/{sid}/summary",
        f"/sessions/{sid}/trades",
        f"/accounts/{account['id']}/ledger",
        f"/accounts/{account['id']}/risk-preview",
        f"/analytics/overview?account_id={account['id']}",
    ]:
        assert client.get("/api/v1" + path).status_code == 404
    assert client.post("/api/v1/journal", json={"title": "Invalid", "content": "Forbidden", "session_id": sid}).status_code == 404
    assert (
        client.post("/api/v1/journal", json={"title": "Invalid", "content": "Forbidden", "trade_id": win.json()["id"]}).status_code == 404
    )
    assert client.get("/api/v1/journal").json() == []
    client.post("/api/v1/auth/logout")


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[db] = override_db
client = TestClient(app)


def setup_user(email):
    with TestingSession() as s:
        user = User(email=email, password_hash=CryptContext(schemes=["bcrypt"]).hash("secret"), name=email)
        s.add(user)
        s.commit()


def login(email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "secret"})
    assert response.status_code == 200
    return response


def test_auth_and_ownership():
    setup_user("a@example.com")
    setup_user("b@example.com")
    assert client.get("/api/v1/auth/me").status_code == 401
    login("a@example.com")
    created = client.post("/api/v1/accounts", json={"name": "A", "initial_balance": "2000.00"})
    assert created.status_code == 200
    login("b@example.com")
    assert client.get("/api/v1/accounts").json() == []


def test_loss_limit_draw_cancelled_and_invalid_trade_values():
    setup_user("limits@example.com")
    login("limits@example.com")
    configure_profile("limits@example.com")
    account = client.post("/api/v1/accounts", json={"name": "Limits", "initial_balance": "2000"}).json()
    params = {"trading_account_id": account["id"]}
    sess = client.post("/api/v1/sessions", json=params).json()
    body = {
        "trading_account_id": account["id"],
        "trading_session_id": sess["id"],
        "symbol": "EURUSD",
        "market_type": "OTC",
        "timeframe": "1m",
        "direction": "PUT",
        "stake": "20",
        "payout_percent": "84",
        "result": "LOSS",
    }
    assert client.post("/api/v1/trades", json={**body, "market_type": "MIXED"}).status_code == 422
    assert client.post("/api/v1/trades", json={**body, "stake": "41"}).status_code == 422
    assert client.post("/api/v1/trades", json=body).status_code == 200
    for stake in ["19.80", "0.20"]:
        assert client.post("/api/v1/trades", json={**body, "stake": stake}).status_code == 200
    summary = client.get(f"/api/v1/sessions/{sess['id']}/summary").json()
    assert summary["limit_reached"] and summary["limit_reason"] == "Maximum session loss reached"
    assert Decimal(summary["remaining_risk"]) == 0
    assert client.post("/api/v1/trades", json=body).status_code == 409
    client.post(f"/api/v1/sessions/{sess['id']}/close")
    second = client.post("/api/v1/sessions", json=params).json()
    for result in ["DRAW", "CANCELLED"]:
        assert (
            client.post("/api/v1/trades", json={**body, "trading_session_id": second["id"], "stake": "19.60", "result": result}).status_code
            == 200
        )
    summary = client.get(f"/api/v1/sessions/{second['id']}/summary").json()
    assert summary["draws"] == summary["cancelled"] == 1
    assert Decimal(summary["net_pnl"]) == 0 and Decimal(summary["win_rate"]) == 0
    client.post("/api/v1/auth/logout")


def test_ledger_session_close_and_idempotency():
    setup_user("c@example.com")
    login("c@example.com")
    configure_profile("c@example.com")
    account = client.post("/api/v1/accounts", json={"name": "C", "initial_balance": "2000.00"}).json()
    session = client.post(
        "/api/v1/sessions",
        json={"trading_account_id": account["id"]},
    ).json()
    trade = client.post(
        "/api/v1/trades",
        json={
            "trading_account_id": account["id"],
            "trading_session_id": session["id"],
            "symbol": "EURUSD",
            "market_type": "REGULAR",
            "timeframe": "1m",
            "direction": "CALL",
            "stake": "20",
            "payout_percent": "84",
            "result": "WIN",
        },
    ).json()
    assert Decimal(trade["profit_loss"]) == Decimal("16.80")
    closed = client.post(f"/api/v1/sessions/{session['id']}/close")
    assert closed.status_code == 200 and closed.json()["status"] == "CLOSED"
    assert client.post(f"/api/v1/sessions/{session['id']}/close").status_code == 200
    summary = client.get(f"/api/v1/sessions/{session['id']}/summary")
    assert summary.status_code == 200 and summary.json()["wins"] == 1 and summary.json()["net_pnl"] == "16.80000000"
    assert (
        client.post(
            "/api/v1/trades",
            json={
                "trading_account_id": account["id"],
                "trading_session_id": session["id"],
                "symbol": "EURUSD",
                "market_type": "REGULAR",
                "timeframe": "1m",
                "direction": "CALL",
                "stake": "20",
                "payout_percent": "84",
                "result": "LOSS",
            },
        ).status_code
        == 409
    )
    with TestingSession() as s:
        account_row = s.scalar(select(TradingAccount).where(TradingAccount.name == "C"))
        assert account_row.current_balance == Decimal("2016.80")
        assert len(s.scalars(select(LedgerEntry).where(LedgerEntry.account_id == account_row.id)).all()) == 2
        assert s.scalar(select(AuditLog).where(AuditLog.event_type == "SESSION_CLOSED")) is not None


def configure_profile(email):
    with TestingSession() as s:
        user = s.scalar(select(User).where(User.email == email))
        s.add(
            RiskProfile(
                user_id=user.id,
                risk_per_trade_percent=Decimal("1"),
                max_session_loss_percent=Decimal("2"),
                max_session_operations=4,
                minimum_payout_percent=Decimal("80"),
            )
        )
        s.commit()
