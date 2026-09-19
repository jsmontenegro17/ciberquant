from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from sqlalchemy import select, func, inspect, text
from sqlalchemy.orm import sessionmaker
from alembic.operations import Operations
from alembic.migration import MigrationContext
from app.models import MarketDataImport, User, AuditLog, Candle, ValidationRun, now
from app.operations import ownership, recover
from test_market_data_migration import migrated_database, migration  # noqa: F401
from test_validation_migration import setup


@pytest.fixture
def operations_db(migrated_database):
    with migrated_database.begin() as c, Operations.context(MigrationContext.configure(c)):
        for rev in ("004_strategy_backtesting", "005_validation", "006_live_scanner", "007_operations"):
            migration(rev).upgrade()
    return migrated_database


def test_007_preserves_raw_and_downgrade_only_heartbeat(operations_db):
    with operations_db.begin() as c, Operations.context(MigrationContext.configure(c)):
        count = c.scalar(select(func.count()).select_from(Candle))
        assert "worker_heartbeats" in inspect(c).get_table_names()
        migration("007_operations").downgrade()
        assert c.scalar(select(func.count()).select_from(Candle)) == count
        assert "scanner_events" in inspect(c).get_table_names()
        migration("007_operations").upgrade()


def require_pg(engine):
    if engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL advisory ownership/concurrent reconciliation; SQLite must not emulate locks")


def test_active_import_not_abandoned_and_concurrent_idempotent_recovery(operations_db):
    engine = operations_db
    require_pg(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        user = User(email="recovery@example.invalid", name="Recovery", password_hash="unused")
        s.add(user)
        s.flush()
        batch = MarketDataImport(
            created_by_user_id=user.id,
            source="TEST",
            broker="TEST",
            symbol="EURUSD",
            market_type="OTC",
            timeframe="1m",
            file_name="test.csv",
            file_sha256="0" * 64,
            started_at=now() - timedelta(days=1),
        )
        s.add(batch)
        s.commit()
        bid = batch.id
    with ownership(engine, "import"):
        assert recover(engine, "import", 0)["status"] == "ACTIVE_OR_RECOVERY_BUSY"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: recover(engine, "import", 0), range(2)))
    assert sum(len(r["recovered"]) for r in results) == 1
    assert recover(engine, "import", 0)["recovered"] == []
    with factory() as s:
        assert s.get(MarketDataImport, bid).status == "FAILED"
        assert s.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.event_type == "JOB_RECOVERED")) == 1


def test_consumed_reveal_recovery_never_reseals_or_reexecutes(operations_db):
    require_pg(operations_db)
    factory, uid, rid = setup(operations_db)
    with operations_db.begin() as c:
        c.execute(text("UPDATE validation_runs SET status='RUNNING_TEST', test_revealed_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": rid})
    assert recover(operations_db, "validation", 0)["recovered"] == [rid]
    from app.validation.repository import reveal
    from fastapi import HTTPException

    with factory() as s:
        r = s.get(ValidationRun, rid)
        assert r.status == "FAILED" and r.test_revealed_at is not None
        assert r.test_summary is None and r.development_summary is not None
        with pytest.raises(HTTPException) as caught:
            reveal(s, uid, rid)
        assert caught.value.status_code == 409
