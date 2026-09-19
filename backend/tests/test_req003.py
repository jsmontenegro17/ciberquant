from pathlib import Path
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.main import app
from app.api.deps import db, current_user
from app.models import User, Candle, MarketDataImport, AuditLog
from app.config import settings
from app.market_data.normalization import Dataset
from app.market_data.providers.csv import CSVMarketDataProvider
from app.market_data.ingestion import ingest
from app.cataloger.engine import analyze

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "market_data"
META = dict(source="MT5", broker="BrokerA", symbol="EURUSD", market_type="REGULAR", timeframe="1m")
HEADER = "open_time,close_time,open,high,low,close,tick_volume,spread\n"
ROW = "2026-09-19T14:00:00Z,2026-09-19T14:01:00Z,1.1000,1.1010,1.0990,1.1008,120,0.0001\n"


@pytest.fixture
def harness():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        admin = User(email="market@example.com", password_hash="unused", name="Market QA", role="ADMIN")
        s.add(admin)
        s.commit()
        admin_id = admin.id

    def test_db():
        with factory() as session:
            yield session

    def actor():
        with factory() as s:
            return s.get(User, admin_id)

    saved = dict(app.dependency_overrides)
    app.dependency_overrides[db] = test_db
    app.dependency_overrides[current_user] = actor
    with TestClient(app) as client:
        yield client, factory, admin_id
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    engine.dispose()


def upload(client, text=None, meta=None, name="fixture.csv"):
    raw = (HEADER + ROW).encode() if text is None else text.encode() if isinstance(text, str) else text
    return client.post("/api/v1/market-data/imports/csv", data=meta or META, files={"file": (name, raw, "text/csv")})


def query(**kw):
    return {**META, "start": "2026-09-18T00:00:00Z", "end": "2026-09-20T00:00:00Z", **kw}


def test_atomic_import_duplicate_conflict_provenance(harness):
    client, factory, uid = harness
    raw = (EXAMPLES / "synthetic_regular.csv").read_bytes()
    first = upload(client, raw, name="../../fixture.csv").json()
    assert first["status"] == "COMPLETED" and first["rows_inserted"] == 30
    assert first["file_name"] == "fixture.csv"
    assert first["file_sha256"] == hashlib.sha256(raw).hexdigest()
    assert first["warnings"][0]["code"] == "GAP"
    again = upload(client, raw).json()
    assert again["rows_inserted"] == 0 and again["rows_duplicates"] == 30
    conflict = raw.decode().replace("1.1008", "1.1007", 1)
    # Include a genuinely new candle before a conflict: no partial persistence.
    earlier = ROW.replace("2026-09-19", "2026-09-17")
    failed = upload(client, HEADER + earlier + "\n".join(conflict.splitlines()[1:])).json()
    assert failed["status"] == "FAILED" and failed["rows_conflicting"] == 1 and failed["rows_inserted"] == 0
    assert failed["errors"][0]["code"] == "DATA_CONFLICT"
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Candle)) == 30
        assert set(s.scalars(select(Candle.import_id))) == {first["id"]}
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 6
        assert s.get(MarketDataImport, failed["id"]).status == "FAILED"
    inspection = client.get("/api/v1/market-data/candles", params=query(limit=2, offset=1)).json()
    assert inspection["total"] == 30 and len(inspection["items"]) == 2
    assert inspection["items"][0]["open_time"].endswith("+00:00")
    history = client.get("/api/v1/market-data/imports?limit=1&offset=1").json()
    assert history["total"] == 3 and len(history["items"]) == 1


@pytest.mark.parametrize(
    "bad",
    [
        ROW + ROW,
        ROW.replace("1.1010", "1.0000"),
        ROW.replace("Z", ""),
        ROW.replace("1.1008", "NaN"),
        ROW.replace("1.1008", "Infinity"),
        ROW.replace("120", "-1"),
        ROW.replace("0.0001", "-0.1"),
        ROW.replace("14:01:00", "13:59:00"),
        ROW.replace("1.1008", "1.10000000001"),
        ROW.replace("1.1008", "0"),
        ROW.replace("1.1008", "100000000000000"),
        ROW.replace("2026-09-19", "2026-09-20") + ROW,
        ROW.replace(",120,0.0001", ""),
    ],
)
def test_invalid_files_are_atomic(harness, bad):
    client, factory, _ = harness
    result = upload(client, HEADER + bad).json()
    assert result["status"] == "FAILED" and result["rows_inserted"] == 0 and result["errors"]
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Candle)) == 0


def test_utc_admin_limits_and_headers(harness, monkeypatch):
    client, factory, uid = harness
    offset = ROW.replace("14:00:00Z", "09:00:00-05:00").replace("14:01:00Z", "09:01:00-05:00")
    assert upload(client, HEADER + offset).json()["rows_inserted"] == 1
    assert upload(client).json()["rows_duplicates"] == 1
    assert upload(client, HEADER.replace("spread", "symbol") + ROW).json()["status"] == "FAILED"
    assert upload(client, b"\x00binary").json()["status"] == "FAILED"
    assert upload(client, HEADER).json()["status"] == "FAILED"
    assert upload(client, meta={**META, "market_type": "MIXED"}).status_code == 422
    monkeypatch.setattr(settings, "market_data_max_rows", 1)
    assert upload(client, (EXAMPLES / "synthetic_regular.csv").read_bytes()).json()["status"] == "FAILED"
    monkeypatch.setattr(settings, "market_data_max_upload_mb", 1)
    assert upload(client, b"x" * (1024 * 1024 + 1)).status_code == 413
    assert upload(client, b"x" * (2 * 1024 * 1024)).status_code == 413
    with factory() as s:
        s.get(User, uid).role = "USER"
        s.commit()
    assert upload(client).status_code == 403
    assert client.get("/api/v1/market-data/coverage").status_code == 200
    assert client.get("/api/v1/market-data/candles", params=query(start="2026-09-18")).status_code == 422


def test_broker_otc_source_timeframe_symbol_isolation(harness):
    client, _, _ = harness
    regular = (EXAMPLES / "synthetic_regular.csv").read_bytes()
    puts = (EXAMPLES / "synthetic_otc.csv").read_bytes()
    assert upload(client, regular).json()["rows_inserted"] == 30
    variants = [{"broker": "BrokerB"}, {"market_type": "OTC"}, {"source": "OTHER"}, {"symbol": "GBPUSD"}, {"timeframe": "5m"}]
    for change in variants:
        assert upload(client, puts, {**META, **change}).json()["rows_inserted"] == 30
    coverage = client.get("/api/v1/market-data/coverage").json()
    assert coverage["total"] == 6
    result = client.get("/api/v1/cataloger/patterns", params=query(pattern_length=3)).json()
    assert result["candles_examined"] == 30
    assert result["eligible_windows"] == 24 and result["windows_skipped_due_to_gaps"] == 3
    assert next(p for p in result["patterns"] if p["pattern"] == "CCC")["next_bearish_count"] == 6
    for change in variants[:-1]:
        separate = client.get("/api/v1/cataloger/patterns", params=query(**change)).json()
        assert [p["pattern"] for p in separate["patterns"]] == ["PPP"]
        assert separate["patterns"][0]["sample_size"] == 24
    five = client.get("/api/v1/cataloger/patterns", params=query(timeframe="M5")).json()
    assert five["eligible_windows"] == 0
    assert client.get("/api/v1/market-data/candles", params=query(limit=1001)).status_code == 422


def fixture_candles():
    return CSVMarketDataProvider(EXAMPLES / "synthetic_regular.csv", Dataset(**META)).get_historical_candles()


def test_catalog_api_direction_contract_without_legacy_aliases(harness):
    client, _, _ = harness
    assert upload(client, (EXAMPLES / "synthetic_regular.csv").read_bytes()).json()["status"] == "COMPLETED"
    response = client.get("/api/v1/cataloger/patterns", params=query(pattern_length=3))
    assert response.status_code == 200
    patterns = response.json()["patterns"]
    # Exact allowlist proves the response contains every direction field and no legacy aliases.
    expected_keys = {
        "pattern",
        "pattern_length",
        "sample_size",
        "next_bullish_count",
        "next_bearish_count",
        "next_doji_count",
        "next_bullish_probability",
        "next_bearish_probability",
        "next_doji_probability",
        "first_observation",
        "last_observation",
        "distinct_days",
    }
    assert patterns and all(set(pattern) == expected_keys for pattern in patterns)
    ccc = next(pattern for pattern in patterns if pattern["pattern"] == "CCC")
    assert ccc["sample_size"] == 6
    assert [ccc[key] for key in ("next_bullish_count", "next_bearish_count", "next_doji_count")] == [0, 6, 0]
    assert [ccc[key] for key in ("next_bullish_probability", "next_bearish_probability", "next_doji_probability")] == ["0", "1", "0"]
    # Mixed outcomes retain fractional probabilities as Decimal strings, too.
    response = client.get("/api/v1/cataloger/patterns", params=query(pattern_length=2))
    assert response.status_code == 200
    cc = next(pattern for pattern in response.json()["patterns"] if pattern["pattern"] == "CC")
    assert cc["sample_size"] == 12
    assert [cc[key] for key in ("next_bullish_count", "next_bearish_count", "next_doji_count")] == [6, 6, 0]
    assert [cc[key] for key in ("next_bullish_probability", "next_bearish_probability", "next_doji_probability")] == ["0.5", "0.5", "0"]


def test_manual_quant_regression():
    result = analyze(fixture_candles(), 3)
    expected = {"CCC": (6, 0, 6, 0), "CCP": (6, 0, 0, 6), "CPD": (4, 4, 0, 0), "DCC": (4, 4, 0, 0), "PDC": (4, 4, 0, 0)}
    assert {
        p["pattern"]: (p["sample_size"], p["next_bullish_count"], p["next_bearish_count"], p["next_doji_count"]) for p in result["patterns"]
    } == expected
    for p in result["patterns"]:
        assert p["distinct_days"] == 2
        assert sum(p[k] for k in ("next_bullish_probability", "next_bearish_probability", "next_doji_probability")) == Decimal(1)
    excluded = analyze(fixture_candles(), 3, False)
    assert excluded["eligible_windows"] == 6 and excluded["windows_skipped_due_to_doji"] == 18
    assert [p["pattern"] for p in excluded["patterns"]] == ["CCC"]


@pytest.mark.parametrize("length,eligible", [(2, 26), (3, 24), (4, 22), (5, 20)])
def test_lengths_and_gap_counts(length, eligible):
    result = analyze(fixture_candles(), length)
    assert result["eligible_windows"] == eligible
    assert result["windows_skipped_due_to_gaps"] == length
    assert sum(p["sample_size"] for p in result["patterns"]) == eligible


def test_gap_outcome_boundary_and_bad_engine_input():
    c = fixture_candles()[0]
    base = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    candles = [replace(c, open_time=base + timedelta(minutes=i), close_time=base + timedelta(minutes=i + 1)) for i in [0, 1, 2, 10, 11]]
    assert analyze(candles, 3)["eligible_windows"] == 0
    assert analyze(candles, 2)["eligible_windows"] == 1
    assert analyze(candles, 2)["windows_skipped_due_to_gaps"] == 2
    for changed in [replace(candles[1], broker="B"), replace(candles[1], market_type="OTC")]:
        with pytest.raises(ValueError):
            analyze([candles[0], changed], 2)
    with pytest.raises(ValueError):
        analyze(list(reversed(candles)), 2)
    with pytest.raises(ValueError):
        analyze(candles, 6)
    assert analyze([], 2)["patterns"] == []


def test_catalog_limit_empty_and_explicit_utc(harness, monkeypatch):
    client, _, _ = harness
    assert client.get("/api/v1/cataloger/patterns", params=query()).json()["patterns"] == []
    upload(client, (EXAMPLES / "synthetic_regular.csv").read_bytes())
    monkeypatch.setattr(settings, "market_data_max_catalog_candles", 20)
    assert client.get("/api/v1/cataloger/patterns", params=query()).status_code == 422


def test_optional_values_and_close_time_conflict(harness):
    client, _, _ = harness
    assert upload(client).json()["status"] == "COMPLETED"
    for changed in [ROW.replace(",120,", ",121,"), ROW.replace("0.0001", "0.0002"), ROW.replace("14:01:00", "14:00:59")]:
        report = upload(client, HEADER + changed).json()
        assert report["status"] == "FAILED" and report["rows_conflicting"] == 1
    assert upload(client).json()["rows_duplicates"] == 1


def test_persistence_error_rolls_back_and_audits(harness, monkeypatch):
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    client, factory, uid = harness

    def reject(mapper, connection, target):
        raise IntegrityError("synthetic insert failure", {}, Exception("test"))

    event.listen(Candle, "before_insert", reject)
    try:
        report = upload(client).json()
        assert report["status"] == "FAILED" and report["rows_inserted"] == 0
        assert report["errors"][0]["code"] == "PERSISTENCE_ERROR"
    finally:
        event.remove(Candle, "before_insert", reject)
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Candle)) == 0
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 2


def test_reads_and_import_require_authentication(harness):
    client, _, _ = harness
    actor = app.dependency_overrides.pop(current_user)
    try:
        assert upload(client).status_code == 401
        for path in [
            "/market-data/coverage",
            "/market-data/imports",
            "/market-data/options",
            "/market-data/candles",
            "/cataloger/patterns",
        ]:
            assert client.get("/api/v1" + path, params=query()).status_code == 401
    finally:
        app.dependency_overrides[current_user] = actor
