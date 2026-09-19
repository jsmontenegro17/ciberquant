from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from alembic.operations import Operations
from alembic.migration import MigrationContext
from app.models import User, Strategy, ValidationRun, ValidationSegment, BacktestRun
from app.strategies.repository import create_version
from app.validation.repository import create, reveal
from test_market_data_migration import migrated_database, migration  # noqa: F401
from test_feature_api import seed
from validation_fixture import data, request
from backtest_fixture import definition


@pytest.fixture
def validation_db(migrated_database):
    with migrated_database.begin() as c, Operations.context(MigrationContext.configure(c)):
        migration("004_strategy_backtesting").upgrade()
        migration("005_validation").upgrade()
    yield migrated_database


def setup(engine):
    factory = sessionmaker(bind=engine)
    seed(factory, data(100))
    with factory() as s:
        u = User(name="Validation", email="validation@example.com", password_hash="unused")
        s.add(u)
        s.flush()
        st = Strategy(user_id=u.id, name="Fixed", status="TESTING")
        s.add(st)
        s.commit()
        v = create_version(s, st.id, u.id, definition())
        run = create(s, u.id, request(100, strategy_version_id=v.id))
        assert run.status == "SEALED", run.error_summary
        return factory, u.id, run.id


def test_005_json_constraints_fks_uniqueness_and_immutability(validation_db):
    factory, uid, rid = setup(validation_db)
    with factory() as s:
        run = reveal(s, uid, rid)
        assert run.status == "COMPLETED"
        assert run.verdict == "INCONCLUSIVE"
        assert run.config_snapshot["protocol"]["validation_engine_version"] == "cq-validation-v1"
        run_id = run.id
        segment = s.scalar(select(ValidationSegment).where(ValidationSegment.validation_run_id == rid))
        values = {c.name: getattr(segment, c.name) for c in ValidationSegment.__table__.columns if c.name != "id"}
    with factory() as s:
        s.add(ValidationSegment(**values))
        with pytest.raises(IntegrityError):
            s.commit()
    for assignment in ["status='INVALID'", "verdict='INVALID'", "test_end=test_start", "expiry_bars=0", "validation_engine_version='v2'"]:
        with validation_db.connect() as c:
            with pytest.raises(IntegrityError):
                c.execute(text(f"UPDATE validation_runs SET {assignment} WHERE id=:id"), {"id": run_id})
            c.rollback()
    if validation_db.dialect.name == "postgresql":
        assert (
            str(next(c for c in inspect(validation_db).get_columns("validation_runs") if c["name"] == "config_snapshot")["type"]) == "JSONB"
        )
        with validation_db.connect() as c:
            with pytest.raises(IntegrityError):
                c.execute(text("UPDATE validation_segments SET validation_run_id=999999 WHERE id=:id"), {"id": values["validation_run_id"]})
            c.rollback()
    for model, key, field, value in [(ValidationRun, run_id, "config_sha256", "bad"), (ValidationSegment, segment.id, "fold_number", 4)]:
        with factory() as s:
            setattr(s.get(model, key), field, value)
            with pytest.raises(ValueError):
                s.commit()
    with factory() as s:
        assert all(b.purpose == "VALIDATION" for b in s.scalars(select(BacktestRun)))
    with validation_db.begin() as c, Operations.context(MigrationContext.configure(c)):
        migration("005_validation").downgrade()
        assert "validation_runs" not in inspect(c).get_table_names()
        migration("005_validation").upgrade()
    with validation_db.connect() as c:
        assert set(c.execute(text("SELECT purpose FROM backtest_runs")).scalars()) == {"MANUAL"}


def test_postgres_concurrent_single_reveal(validation_db):
    if validation_db.dialect.name != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL")
    factory, uid, rid = setup(validation_db)
    barrier = Barrier(2)

    def work(_):
        with factory() as s:
            barrier.wait(timeout=10)
            try:
                return reveal(s, uid, rid).status
            except HTTPException as e:
                return e.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(work, range(2)))
    assert sorted(map(str, outcomes)) == ["409", "COMPLETED"]
