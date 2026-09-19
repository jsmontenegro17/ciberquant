# REQ-003 — Market Data Ingestion & Candle Cataloger

Status: IN_PROGRESS
Priority: P1
Classification: LARGE
Created: 2026-09-19
Target version: 0.3.0-dev
Base: main / v0.2.0
Branch: codex/req-003-market-data-cataloger

## Objective and scope

Auditable immutable historical candles, atomic admin-only CSV ingestion, import provenance, data quality and coverage, paginated inspection, deterministic C/P/D sequences of length 2–5, descriptive next-candle statistics and connected Market Data/Cataloger screens. No strategies, indicators, integrations, streaming, backtesting, ML or trading recommendations.

## Acceptance contract

- Dataset identity is source/broker/symbol/market_type/timeframe; candle identity adds UTC open_time. Broker is non-null (UNSPECIFIED when absent). ORM and migration agree.
- One CSV per dataset, aware timestamps only, Decimal parsing, positive valid OHLC, nonnegative optional volume/spread, chronological order and configurable byte/row limits.
- Same-file duplicate or invalid data rejects the entire batch. Exact database duplicates are counted; conflicting values fail without modifying existing candles or inserting partial data.
- Imports retain actor, checksum, sanitized filename, metadata, counters, timestamps, errors/warnings and audit events. CSV candles reference their original batch; uploads are not retained.
- ADMIN imports; authenticated users read. History and inspection are paginated, dataset/date filters restrict queries.
- Pure linear catalog engine requires one dataset and consecutive open_time intervals across pattern and outcome. Never crosses gaps or mixes brokers/OTC/timeframes. include_doji=false excludes D anywhere in the whole window, including outcome.
- Counts are integers; probabilities Decimal; observation dates refer to outcome open_time in UTC. Patterns sorted lexicographically. No confidence, profitability or recommendation claims.
- Deterministic manual fixtures, UTC, authorization, duplicate/conflict/atomicity, isolation, lengths 2–5, gaps and doji tests; frontend tests and disposable browser E2E. Existing REQ-002 tests retained.
- PostgreSQL migration, backend, frontend/E2E, Docker and final-head CI PASS before QA. PR remains open pending human acceptance; no automatic merge or tag.

## Design decisions

Optional hour/day filters and single-pattern inspection are deferred. Date ranges are inclusive start/exclusive end and apply to every candle in each window. Bounded V1 imports and catalog queries avoid unbounded resource usage. Exact duplicate comparison includes close_time, OHLC and optional volume/spread. Numeric values exceeding storage precision are rejected rather than rounded silently.

## Implementation sequence

Identity/provenance and migration → ingestion/quality → pure cataloger → APIs → UI → deterministic/regression/E2E tests → documentation → PR/CI → QA.

## Risks and rollback

No production deployment claim; SEC-001 remains separate. Migration downgrade must refuse when old broker-less uniqueness would lose information. Raw candles are append-only; no edit/delete API. Revert feature before integration; schema rollback is explicitly reviewed and may discard new import metadata only after operator backup.

## Evidence

Local implementation checkpoint 2026-09-19:46 backend tests PASS/3 PostgreSQL-only or nonapplicable cases skipped,18 frontend tests PASS,2 browser E2E PASS (REQ-002 preserved), typecheck/lint/build PASS. Desktop/tablet screenshots inspected with no page overflow. PostgreSQL/Docker CI and PR pending. Human Acceptance: PENDING.

Manual deterministic fixture: two days of CCCPD repeated three times/day.30 total candles. Length3 CCC samples6/nextP6; CCP samples6/nextD6; CPD,DCC,PDC each samples4/nextC4.24 eligible windows and3 gap-skipped. Separate OTC/broker/source/symbol/timeframe queries verified. include_doji=false yields6 eligible/18 doji-skipped.

Performance:100,000 synthetic candles (6,560,041-byte CSV), pure engine0.9356s, temporary SQLite ingestion7.7322s,99,997 eligible windows on this workstation. Reproduce with backend/scripts/benchmark_cataloger.py; not a production SLA. Engine traverses linearly; identity B-tree supports database range filtering.

## Known limitations

Synchronous bounded V1 imports; infrastructure/process interruption can leave a visible PROCESSING batch requiring operator investigation/reimport (idempotent). No background worker/recovery UI. Optional hour/day filters deferred. Existing auth dependency warnings and SEC-001 production hardening remain separate debt. No known functional P0/P1 in locally validated scope; final PostgreSQL/Docker validation still required before QA.
