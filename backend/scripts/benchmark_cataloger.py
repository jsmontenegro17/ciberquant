"""REQ-003 reproducible synthetic benchmark; temporary database only. Run from backend."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta
from time import perf_counter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import Base
from app.models import User
from app.market_data.normalization import Dataset
from app.market_data.providers.csv import csv_reader, parse_row
from app.market_data.ingestion import ingest
from app.cataloger.engine import analyze

size = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
dataset = Dataset(source="SYNTHETIC_BENCHMARK", broker="DEMO", symbol="EURUSD", market_type="REGULAR", timeframe="1m")
start = datetime(2026, 1, 1, tzinfo=timezone.utc)
rows = ["open_time,close_time,open,high,low,close"]
for i in range(size):
    t = start + timedelta(minutes=i)
    close = ("1.1", "1.1", "1.1", "0.9", "1")[i % 5]
    rows.append(f"{t.isoformat()},{(t + timedelta(minutes=1)).isoformat()},1,1.2,0.8,{close}")
raw = ("\n".join(rows) + "\n").encode()
candles = [parse_row(row, dataset) for row in csv_reader(raw)]
timer = perf_counter()
result = analyze(candles, 3)
catalog_seconds = perf_counter() - timer
assert result["candles_examined"] == size and result["eligible_windows"] == size - 3
with TemporaryDirectory(prefix="cq-benchmark-") as folder:
    engine = create_engine("sqlite:///" + str(Path(folder) / "benchmark.db"))
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="benchmark@example.com", password_hash="unused", name="Benchmark", role="ADMIN")
        session.add(user)
        session.commit()
        uid = user.id
        timer = perf_counter()
        batch = ingest(session, uid, dataset, raw, "synthetic.csv", size)
        ingestion_seconds = perf_counter() - timer
        assert batch.status == "COMPLETED" and batch.rows_inserted == size
    engine.dispose()
print(
    json.dumps(
        {
            "dataset_size": size,
            "csv_bytes": len(raw),
            "catalog_seconds": round(catalog_seconds, 4),
            "ingestion_seconds_sqlite": round(ingestion_seconds, 4),
            "eligible_windows": result["eligible_windows"],
        }
    )
)
