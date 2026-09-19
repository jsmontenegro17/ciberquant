# Market Data

REQ-003 introduces auditable append-only ingestion. Source, broker, symbol, market_type and timeframe identify one dataset; UTC open_time completes candle identity. Text labels are trimmed/uppercased; blank broker becomes UNSPECIFIED. Timeframe aliases use one backend parser (1m/5m/15m/30m/1h; M1/M5/M15/M30/H1 accepted).

## Architecture

- `app/market_data/providers/`: base contract, Mock and CSV. Foundation imports remain compatible through `app/services/market_data.py`.
- `normalization.py`, `timeframe.py`, `quality.py`: canonical identity, UTC, exact Decimal storage validation.
- `ingestion.py`: validation, conflict detection, transactional persistence and audit.
- `repository.py`: database filtering, coverage and PostgreSQL per-dataset transaction advisory locks.
- `upload_limit.py`: bounded streamed multipart requests.
- `app/api/market_data.py`: authenticated APIs; reusable require_admin protects imports.

## Persistence and migration

Migration 003 creates market_data_imports (JSONB quality report in PostgreSQL), candle import_id FK, non-null broker and the six-column unique identity. Its unique B-tree supports dataset equality + open_time range scans; a created_at/id index supports import history. ORM matches these constraints/indexes.

Migration normalizes existing dataset labels/aliases, never OHLC/timestamps. PostgreSQL migration rolls back if canonical identities collide: investigate before retry, never silently delete records. Legacy candles retain null import_id. Downgrade refuses broker-less collisions and otherwise removes provenance metadata (backup required); it does not restore original label casing or broker nulls.

## Atomicity and provenance

A PROCESSING batch and STARTED audit event are committed first. Validate all rows, compare existing values, insert new candles and finalize COMPLETED/audit in one transaction. Any validation/conflict/insert failure leaves zero new candles and a FAILED batch/audit. Concurrent PostgreSQL imports of one dataset are serialized even when no candles existed. No edit/delete candle endpoints.

Identical timestamps and all stored values = duplicate; different OHLC, close_time, volume or spread = DATA_CONFLICT. Existing candles/provenance never change. File duplicate identities, unsorted rows, invalid OHLC/time/numeric fields reject the whole batch.

Reports retain filename basename, SHA-256, actor, metadata, timestamps and received/valid/inserted/duplicate/rejected/conflicting counts; up to 100 error and warning details (500 characters per error). Rejected counts invalid rows, not otherwise-valid rows rolled back. For row-limit failures, received counts rows read through the first excess row. Gap warnings do not reject ingestion.

If the process/database fails before finalization, the persisted PROCESSING batch is visibly unfinished. Check history before reimport; reimport is idempotent. Automated recovery/background job management is future scope. The upload is closed after bounded reading and not retained; multipart may use temporary spooling.

## APIs

- POST /api/v1/market-data/imports/csv: ADMIN, multipart file + dataset metadata. Batch outcomes (including FAILED with concrete errors) return 200; authorization 401/403, invalid metadata 422, oversized upload 413.
- GET /api/v1/market-data/imports: authenticated; limit 1–100/default20, offset, total/items.
- GET /api/v1/market-data/coverage: authenticated; limit 1–500/default100, offset, total/items, grouped identity/count/first/last.
- GET /api/v1/market-data/candles: full dataset + aware start/end required; [start,end) by open_time; limit 1–1000/default100, offset, total/items with provenance.
- GET /api/v1/market-data/options: canonical timeframes, market types, upload/row limits.

See [CSV format](../MARKET_DATA_CSV_FORMAT.md). Defaults: MARKET_DATA_MAX_UPLOAD_MB=20, MARKET_DATA_MAX_ROWS=100000, MARKET_DATA_MAX_CATALOG_CANDLES=250000. Limits are environment-configurable and passed through Compose. Total multipart body allows file limit + 64 KiB metadata; file bytes independently capped. Strict UTF-8 CSV content, not filename/MIME trust. Only ADMIN can mutate the global market dataset.
