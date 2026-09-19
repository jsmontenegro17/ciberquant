"""Isolated migration harness; PostgreSQL is mandatory in CI, SQLite exercises local rollback."""

import importlib.util
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import create_engine, inspect, text, select, func
from sqlalchemy.orm import sessionmaker
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.config import settings
from app.models import User, Candle
from app.market_data.normalization import Dataset
from app.market_data.ingestion import ingest

VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def migration(name):
    spec = importlib.util.spec_from_file_location(name, VERSIONS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["sqlite", "postgresql"])
def migrated_database(request):
    postgres = request.param == "postgresql"
    if postgres and os.environ.get("CI_MARKET_DATA_POSTGRES_TESTS") != "true":
        pytest.skip("PostgreSQL migration/concurrency checks require explicit disposable CI service")
    root = create_engine(settings.database_url if postgres else "sqlite://")
    schema = "req003_test_" + uuid4().hex
    if postgres:
        assert root.dialect.name == "postgresql"
        with root.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(settings.database_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = root
    try:
        with engine.begin() as conn:
            with Operations.context(MigrationContext.configure(conn)):
                migration("001_initial").upgrade()
                migration("002_req002_session_snapshot").upgrade()
                conn.execute(
                    text("""INSERT INTO candles
                    (source,broker,symbol,market_type,timeframe,open_time,close_time,open,high,low,close,created_at)
                    VALUES ('mt5',NULL,'legacy','regular','M1','2026-09-19 14:00:00+00:00','2026-09-19 14:01:00+00:00',1,2,1,2,'2026-09-19 14:00:00+00:00')""")
                )
                migration("003_market_data").upgrade()
        yield engine
    finally:
        if postgres:
            engine.dispose()
            # Only the UUID-named test-owned schema is removed.
            with root.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        root.dispose()


def test_migration_alignment_and_safe_downgrade(migrated_database):
    engine = migrated_database
    inspector = inspect(engine)
    constraint = next(x for x in inspector.get_unique_constraints("candles") if x["name"] == "uq_candle_identity")
    assert constraint["column_names"] == ["source", "broker", "symbol", "market_type", "timeframe", "open_time"]
    assert not next(x for x in inspector.get_columns("candles") if x["name"] == "broker")["nullable"]
    assert any(x["name"] == "ix_market_data_imports_created_at" for x in inspector.get_indexes("market_data_imports"))
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT broker FROM candles")) == "UNSPECIFIED"
    with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
        migration("003_market_data").downgrade()
    assert "market_data_imports" not in inspect(engine).get_table_names()
    with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
        migration("003_market_data").upgrade()
    factory = sessionmaker(bind=engine)
    with factory() as session:
        # Copy stored timestamps exactly (SQLite's text representation differs from PostgreSQL).
        session.execute(
            text("""INSERT INTO candles
            (source,broker,symbol,market_type,timeframe,open_time,close_time,open,high,low,close,created_at)
            SELECT source,'OTHER',symbol,market_type,timeframe,open_time,close_time,open,high,low,close,created_at
            FROM candles WHERE symbol='LEGACY'""")
        )
        session.commit()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
            migration("003_market_data").downgrade()


def test_postgres_concurrent_idempotency_and_exact_numeric(migrated_database):
    engine = migrated_database
    if engine.dialect.name != "postgresql":
        pytest.skip("Advisory lock and exact NUMERIC require PostgreSQL")
    factory = sessionmaker(bind=engine)
    with factory() as session:
        user = User(name="Import test", email="test@example.com", password_hash="unused", role="ADMIN")
        session.add(user)
        session.commit()
        uid = user.id
    dataset = Dataset(source="MT5", broker="B", symbol="EURUSD", market_type="REGULAR", timeframe="1m")
    raw = b"open_time,close_time,open,high,low,close\n2026-09-19T14:00:00Z,2026-09-19T14:01:00Z,12345678901234.1234567890,12345678901235,12345678901233,12345678901234.1234567891\n"
    barrier = Barrier(2)

    def run():
        with factory() as session:
            barrier.wait(timeout=10)
            batch = ingest(session, uid, dataset, raw, "precision.csv", 100)
            return batch.status, batch.rows_inserted, batch.rows_duplicates

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert sorted(results) == [("COMPLETED", 0, 1), ("COMPLETED", 1, 0)]
    with factory() as session:
        candle = session.scalar(select(Candle).where(Candle.symbol == "EURUSD"))
        assert candle.close == Decimal("12345678901234.1234567891")
        assert session.scalar(select(func.count()).select_from(Candle).where(Candle.symbol == "EURUSD")) == 1
