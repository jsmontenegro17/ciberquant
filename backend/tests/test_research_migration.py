from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from dataclasses import replace
from datetime import timedelta
from sqlalchemy import inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from alembic.operations import Operations
from alembic.migration import MigrationContext
from app.models import User, Strategy, StrategyVersion, BacktestTrade
from app.strategies.repository import create_version
from app.backtesting.repository import run_backtest
from backtest_fixture import definition, config, candles, BASE
from test_feature_api import seed
from test_market_data_migration import migrated_database, migration  # noqa: F401


@pytest.fixture
def research_db(migrated_database):
    with migrated_database.begin() as c, Operations.context(MigrationContext.configure(c)):
        migration("004_strategy_backtesting").upgrade()
        migration("005_validation").upgrade()
    yield migrated_database


def test_migration_constraints_json_persistence_and_downgrade(research_db):
    factory = sessionmaker(bind=research_db)
    seed(factory, candles())
    with factory() as s:
        user = User(name="Research", email="research@example.com", password_hash="unused")
        s.add(user)
        s.flush()
        strategy = Strategy(user_id=user.id, name="Test")
        s.add(strategy)
        s.commit()
        uid, sid = user.id, strategy.id
        version = create_version(s, sid, uid, definition())
        run = run_backtest(s, uid, config(strategy_version_id=version.id))
        assert run.status == "COMPLETED" and run.metrics["trades_executed"] == 5
        assert run.strategy_snapshot["condition_tree"] == definition().snapshot()["condition_tree"]
        assert s.scalar(select(BacktestTrade).where(BacktestTrade.backtest_run_id == run.id)).unit_pnl.as_tuple().exponent == -8
        version_id = version.id
        original_metrics = run.metrics
        ceiling = run.as_of_candle_id
        original_hash = run.config_sha256
    first = candles()[0]
    seed(factory, [replace(first, open_time=BASE - timedelta(minutes=1), close_time=BASE)])
    with factory() as s:
        replay = run_backtest(s, uid, config(strategy_version_id=version_id, as_of_candle_id=ceiling))
        assert replay.metrics == original_metrics and replay.config_sha256 == original_hash
        other = User(name="Other", email="other@example.com", password_hash="unused", role="ADMIN")
        s.add(other)
        s.commit()
        with pytest.raises(HTTPException) as denied:
            run_backtest(s, other.id, config(strategy_version_id=version_id))
        assert denied.value.status_code == 404
    with factory() as s:
        original = s.scalar(select(BacktestTrade))
        values = {c.name: getattr(original, c.name) for c in BacktestTrade.__table__.columns if c.name != "id"}
        values.update(sequence_no=999, entry_time=original.signal_time - timedelta(seconds=1))
        s.add(BacktestTrade(**values))
        with pytest.raises(IntegrityError):
            s.commit()
    with factory() as s:
        v = s.get(StrategyVersion, version_id)
        s.add(StrategyVersion(strategy_id=sid, version=1, **definition().snapshot(), definition_sha256=v.definition_sha256))
        with pytest.raises(IntegrityError):
            s.commit()
    indexes = inspect(research_db).get_indexes("backtest_trades")
    assert any(i["name"] == "ix_backtest_trade_signal" for i in indexes)
    with factory() as s:
        s.add(Strategy(user_id=uid, name="Invalid", status="VALIDATED"))
        with pytest.raises(IntegrityError):
            s.commit()
    if research_db.dialect.name == "postgresql":
        assert (
            str(next(c for c in inspect(research_db).get_columns("backtest_runs") if c["name"] == "strategy_snapshot")["type"]) == "JSONB"
        )
    with research_db.begin() as c, Operations.context(MigrationContext.configure(c)):
        migration("005_validation").downgrade()
        migration("004_strategy_backtesting").downgrade()
    assert "backtest_runs" not in inspect(research_db).get_table_names()
    assert "candles" in inspect(research_db).get_table_names()


def test_postgres_concurrent_version_numbers(research_db):
    if research_db.dialect.name != "postgresql":
        pytest.skip("Row locks require PostgreSQL")
    factory = sessionmaker(bind=research_db)
    with factory() as s:
        user = User(name="Concurrent", email="concurrent@example.com", password_hash="unused")
        s.add(user)
        s.flush()
        strategy = Strategy(user_id=user.id, name="Concurrent")
        s.add(strategy)
        s.commit()
        uid, sid = user.id, strategy.id
    barrier = Barrier(2)

    def work(_):
        with factory() as s:
            barrier.wait(timeout=10)
            return create_version(s, sid, uid, definition()).version

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(work, range(2))) == [1, 2]
