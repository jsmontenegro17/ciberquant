import csv
import hashlib
from dataclasses import asdict
from sqlalchemy.exc import SQLAlchemyError
from ..models import MarketDataImport, Candle, AuditLog, now
from .providers.csv import csv_reader, parse_row
from .quality import validate_candle, VALUE_FIELDS
from .normalization import stored_utc
from .timeframe import duration
from .repository import lock_dataset, existing_for


def audit(session, batch, event):
    session.add(
        AuditLog(
            user_id=batch.created_by_user_id,
            event_type="MARKET_DATA_IMPORT_" + event,
            entity_type="market_data_import",
            entity_id=batch.id,
            metadata_json={"sha256": batch.file_sha256, "status": batch.status},
        )
    )


def safe_name(name):
    name = (name or "upload.csv").replace("\\", "/").split("/")[-1]
    return "".join(c for c in name if c.isprintable())[:255] or "upload.csv"


def ingest(session, actor_id, dataset, raw, filename, max_rows):
    batch = MarketDataImport(
        created_by_user_id=actor_id, **dataset.model_dump(), file_name=safe_name(filename), file_sha256=hashlib.sha256(raw).hexdigest()
    )
    session.add(batch)
    session.flush()
    audit(session, batch, "STARTED")
    session.commit()  # Provenance survives a rejected or rolled-back candle transaction.
    batch_id = batch.id
    counts = dict(rows_received=0, rows_valid=0, rows_inserted=0, rows_duplicates=0, rows_rejected=0, rows_conflicting=0)
    errors, warnings, candles, seen = [], [], [], set()

    def error(code, row, message):
        if len(errors) < 100:
            errors.append({"code": code, "row": row, "message": message[:500]})

    try:
        reader = csv_reader(raw)
        previous = None
        for number, row in enumerate(reader, start=2):
            counts["rows_received"] += 1
            if counts["rows_received"] > max_rows:
                error("ROW_LIMIT", number, f"Maximum {max_rows} data rows")
                counts["rows_rejected"] += 1
                break
            try:
                candle = parse_row(row, dataset)
                issues = validate_candle(candle)
                if candle.open_time in seen:
                    issues.append("Duplicate identity within the same file")
                seen.add(candle.open_time)
                if previous is not None and candle.open_time <= previous:
                    issues.append("Rows must be strictly chronological")
                if previous is not None and candle.open_time > previous + duration(dataset.timeframe) and len(warnings) < 100:
                    warnings.append({"code": "GAP", "row": number, "message": f"Gap after {previous.isoformat()}"})
                previous = candle.open_time
                if issues:
                    raise ValueError("; ".join(issues))
                candles.append(candle)
                counts["rows_valid"] += 1
            except (ValueError, TypeError, OverflowError) as exc:
                counts["rows_rejected"] += 1
                error("INVALID_ROW", number, str(exc))
        if counts["rows_received"] == 0:
            error("EMPTY_FILE", None, "No data rows")
    except (ValueError, csv.Error) as exc:
        error("INVALID_CSV", None, str(exc))
    if not errors:
        try:
            lock_dataset(session, dataset)
            existing = existing_for(session, dataset, candles)
            new = []
            for c in candles:
                old = existing.get(c.open_time)
                if old is None:
                    new.append(c)
                elif stored_utc(old.close_time) == c.close_time and all(getattr(old, k) == getattr(c, k) for k in VALUE_FIELDS):
                    counts["rows_duplicates"] += 1
                else:
                    counts["rows_conflicting"] += 1
                    changed = [k for k in VALUE_FIELDS if getattr(old, k) != getattr(c, k)]
                    if stored_utc(old.close_time) != c.close_time:
                        changed.append("close_time")
                    error("DATA_CONFLICT", None, f"{c.open_time.isoformat()} conflicts with candle {old.id}; fields: {', '.join(changed)}")
            if not errors:
                # Flush bounded chunks; all chunks share one transaction.
                for offset in range(0, len(new), 1000):
                    session.add_all([Candle(**asdict(c), import_id=batch_id) for c in new[offset : offset + 1000]])
                    session.flush()
                counts["rows_inserted"] = len(new)
        except SQLAlchemyError:
            session.rollback()
            counts["rows_inserted"] = 0
            error("PERSISTENCE_ERROR", None, "Import rolled back; retry or contact an administrator")
    if errors:
        session.rollback()
        counts["rows_inserted"] = 0
    batch = session.get(MarketDataImport, batch_id)
    for key, value in counts.items():
        setattr(batch, key, value)
    batch.status = "FAILED" if errors else "COMPLETED"
    batch.completed_at = now()
    batch.error_summary = {"errors": errors, "warnings": warnings, "details_limit": 100}
    audit(session, batch, "FAILED" if errors else "COMPLETED")
    session.commit()
    session.refresh(batch)
    return batch
