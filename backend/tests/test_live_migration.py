import pytest
from sqlalchemy import inspect, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from alembic.operations import Operations
from alembic.migration import MigrationContext
from app.models import Candle, LiveObservation, User, ScannerWatchlist, ScannerWatchItem
from app.live.persistence import persist_closed
from app.market_data.normalization import Dataset
from test_market_data_migration import migrated_database, migration  # noqa: F401
from backtest_fixture import candles, META


def test_006_migration_provenance_constraints_and_downgrade(migrated_database):
    engine = migrated_database
    with engine.begin() as c, Operations.context(MigrationContext.configure(c)):
        for rev in ("004_strategy_backtesting", "005_validation", "006_live_scanner"):
            migration(rev).upgrade()
    factory = sessionmaker(bind=engine)
    rows = candles()
    with factory() as s:
        for _ in range(2):
            persist_closed(s, Dataset(**META), rows, "REPLAY", "REPLAY", rows[-1].close_time, rows[-1].close_time)
            s.commit()
        assert s.scalar(select(func.count()).select_from(Candle).where(Candle.source == META["source"])) == len(rows)
        assert s.scalar(select(func.count()).select_from(LiveObservation)) == len(rows)
        observation = s.scalar(select(LiveObservation))
        values = {c.name: getattr(observation, c.name) for c in LiveObservation.__table__.columns if c.name != "id"}
        oid = observation.id
    with factory() as s:
        s.add(LiveObservation(**values))
        with pytest.raises(IntegrityError):
            s.commit()
    with factory() as s:
        s.get(LiveObservation, oid).mode = "LIVE"
        with pytest.raises(ValueError):
            s.commit()
    if engine.dialect.name == "postgresql":
        assert str(next(c for c in inspect(engine).get_columns("scanner_events") if c["name"] == "evidence")["type"]) == "JSONB"
    with engine.begin() as c, Operations.context(MigrationContext.configure(c)):
        migration("006_live_scanner").downgrade()
        assert "scanner_events" not in inspect(c).get_table_names()
        assert "candles" in inspect(c).get_table_names()
        migration("006_live_scanner").upgrade()
