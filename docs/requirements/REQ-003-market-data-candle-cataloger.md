# REQ-003 — Market Data Ingestion & Candle Cataloger

Status: DONE
Human Acceptance: PASS
Accepted: 2026-09-19
Approved implementation head: b460d3ed9fc21011fff44398b6c202aa0f1f276f
Priority: P1
Classification: LARGE
Created: 2026-09-19
Release version: 0.3.0
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
- PostgreSQL migration, backend, frontend/E2E, Docker and final-head CI PASS. Human acceptance PASS authorizes release closure: final documentation/version CI → PR merge → main CI → tag on the integrated validated commit.

## Design decisions

### Final Human Review — semantic contract correction

Final semantic correction accepted PASS. Direction statistics use `next_bullish_count`, `next_bearish_count`, `next_bullish_probability` and `next_bearish_probability`; doji fields and C/P/D codes retained. No legacy aliases. C = bullish candle, P = bearish candle, D = exact doji. Candle direction describes open→close, not a binary trade result: this is an accepted architectural boundary for future requirements. No mathematical, engine, ingestion or database changes; no new migration. Exact API contract regression, frontend types/consumers and the future BinaryOutcome boundary are validated. REQ-004 is not started.

Correction validation: local backend 47 PASS / 3 PostgreSQL-only or nonapplicable skips; frontend 18 PASS; E2E 2 PASS; lint/typecheck/build PASS. Exact API field allowlist excludes all legacy aliases. CCC remains sample_size=6, bullish=0, bearish=6, doji=0 with probabilities 0/1/0; CC remains 12 samples, counts 6/6/0 and probabilities 0.5/0.5/0. Global repository search finds no obsolete contract identifiers. Accepted correction CI [35457561250](https://github.com/jsmontenegro17/ciberquant/actions/runs/35457561250): backend 49 PASS / 1 intentional SQLite concurrency skip, frontend/E2E and Docker PASS.

Optional hour/day filters and single-pattern inspection are deferred. Date ranges are inclusive start/exclusive end and apply to every candle in each window. Bounded V1 imports and catalog queries avoid unbounded resource usage. Exact duplicate comparison includes close_time, OHLC and optional volume/spread. Numeric values exceeding storage precision are rejected rather than rounded silently.

## Implementation sequence

Identity/provenance and migration → ingestion/quality → pure cataloger → APIs → UI → deterministic/regression/E2E tests → documentation → PR/CI → QA.

## Risks and rollback

No production deployment claim; SEC-001 remains separate. Migration downgrade must refuse when old broker-less uniqueness would lose information. Raw candles are append-only; no edit/delete API. Revert feature before integration; schema rollback is explicitly reviewed and may discard new import metadata only after operator backup.

## Evidence

Historical implementation checkpoint 2026-09-19: 46 backend tests PASS/3 PostgreSQL-only or nonapplicable cases skipped, 18 frontend tests PASS, 2 browser E2E PASS (REQ-002 preserved), typecheck/lint/build PASS. Desktop/tablet screenshots inspected with no page overflow. Final Human Acceptance: PASS, including all integrity, provenance, migration, ingestion, isolation, precision, quant, UI and operational criteria and the semantic correction.

Remote implementation CI: [35456931568](https://github.com/jsmontenegro17/ciberquant/actions/runs/35456931568), commit `c117822487802b42544f01b28d29123a61aab04d`: Backend PASS (48 tests, 1 intentional SQLite concurrency skip), Frontend/E2E PASS, Docker build/Compose startup PASS. PostgreSQL 001→002→003, migration roundtrip/refusal, concurrent duplicate imports and exact NUMERIC storage all validated. Pull-request CI 35456933449 also PASS. [PR #2](https://github.com/jsmontenegro17/ciberquant/pull/2) remains open; final-head CI evidence is recorded in its description to avoid self-referencing commit changes.

## Acceptance scenarios

| Scenario | Result | Evidence |
|---|---|---|
| A — ADMIN import | PASS | 30 candles, original batch FK, SHA-256, coverage and audit; browser report COMPLETED |
| B — reimport | PASS | 0 inserts / 30 duplicates; original provenance retained |
| C — conflict | PASS | FAILED/DATA_CONFLICT, no partial inserts, original values preserved; OHLC/volume/spread/close-time conflicts tested |
| D — catalog | PASS | Exact multiple-pattern counts and Decimal probabilities; CCC samples6/nextP6 in browser |
| E — gap | PASS | 3 excluded length3 windows; explicit10:02→10:10 fixture never bridged |
| F — OTC | PASS | OTC and REGULAR queried independently; broker/source/symbol/timeframe isolation also tested |
| Security | PASS | ADMIN-only mutations; USER403 and unauthenticated401; bounded request/file/rows |
| Delivery | PASS | Migration, backend, frontend/E2E, Docker, docs and PR; final Human Acceptance PASS |

Manual deterministic fixture: two days of CCCPD repeated three times/day.30 total candles. Length3 CCC samples6/nextP6; CCP samples6/nextD6; CPD,DCC,PDC each samples4/nextC4.24 eligible windows and3 gap-skipped. Separate OTC/broker/source/symbol/timeframe queries verified. include_doji=false yields6 eligible/18 doji-skipped.

Performance:100,000 synthetic candles (6,560,041-byte CSV), pure engine0.9356s, temporary SQLite ingestion7.7322s,99,997 eligible windows on this workstation. Reproduce with backend/scripts/benchmark_cataloger.py; not a production SLA. Engine traverses linearly; identity B-tree supports database range filtering.

## Known limitations

P0: none known in validated scope. P1: none known in validated scope. P2: [DATA-001 — Market Data Import Recovery](../debt/DATA-001-stale-processing-import-recovery.md), dependency warnings and [SEC-001](../debt/SEC-001-production-auth-configuration.md). Optional hour/day filters remain deferred. No recovery implementation is included in this release closure. REQ-004 not started.

## Final integration evidence

[REQ-003 release evidence in PR #2](https://github.com/jsmontenegro17/ciberquant/pull/2#issuecomment-5743858785) records the actual integrated main SHA, post-merge CI run ID/results and verified v0.3.0 tag after validation. This linked evidence avoids a self-referential commit changing the SHA being certified. Final documentation/version changes are limited to release closure; feature branch retained through verification.
