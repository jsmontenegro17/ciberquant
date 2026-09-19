# Testing

## REQ-005

`test_backtest_engine.py`: six CALL/PUT outcome cases, exact83.5→0.835, entry105 vs signal close100, bearish expiry/PUT LOSS, expiry2, signal availability, entry/expiry gaps, overlap5(ALLOW15 vs SKIP3), fully resolved range, no future data, warmup/CCC/bars_ago, field comparisons, three-state groups, future mutation, manual metrics/streaks/drawdown, bounded invalid DSL and caps. Synthetic prices are test observations, not market claims.

`test_research_api.py`: owned versions/runs even for ADMIN, definitions/auth/status restrictions, replay after backfill, version immutability, hashes, audit events, exact P&L and no ledger access; cap failures and injected persistence failure leave no partial evidence; ORM mutation guards; five dataset dimensions and64KiB request limit.

`test_research_migration.py`: isolated migration001→004 on SQLite and CI PostgreSQL, indexes/unique constraints, JSONB, exact unit storage, persisted run/replay, PostgreSQL concurrent version numbering and downgrade preserving raw tables. PostgreSQL-only cases skip locally; CI opt-in service executes them.

Frontend tests cover creation, indicator/condition builder, typed constants, field comparisons, bars_ago, immutable-version submission, explicit run setup, payout warning, IN-SAMPLE badge, result/equity/inspector and errors. `research.spec.ts` performs USER login→create DRAFT→RSI2/BB2 conditions→v1→backtest on a preseeded disposable manual fixture→inspect trade. Expected3 trades: DRAW0,LOSS-1,WIN+0.835; total-0.165, unavailable2. No strategy seeded. Existing3 E2Es preserved.

Benchmark: `cd backend; python scripts/benchmark_backtest.py`.100,000 synthetic candles, STANDARD, rule rsi14>=50 CALL,94,243 trades. Windows11 build26200, Intel64 Family6 Model151 Stepping2,20 logical CPUs, Python3.12.14, one process. Features3.696s, signal evaluation0.391s, execution2.375s, total6.738s (includes generation and metrics, excludes SQL/JSON). Pure-engine trade cap explicitly100000 for benchmark; API default remains10000. Measurement, not SLA. Final local/CI evidence is in REQ-005.

## REQ-004

`test_features.py` freezes manual SMA/EMA/RSI/ATR/population-Bollinger fixtures, null warmups, zero-range ratios, RSI100/0/50, gap continuity without resets, Decimal context isolation, serialized rounding, strict identities/specs, prefix100/200 and future-mutation invariance. Fixture closes1..100: EMA20 seed10.5 at index19; serialized EMA20=90.5 at index99; RSI14=100 from index14. Recurrence uses50-digit Decimal, no intermediate quantization; compare canonical18-fractional-digit strings at API boundaries.

`test_feature_api.py` verifies USER access, definitions, range independence(start50/80), no raw writes, snapshot replay after earlier backfill and later candles, all five dataset dimensions, exact caps, empty data and invalid input. Snapshot replay runs on migrated SQLite locally and PostgreSQL in CI using the existing disposable harness; no new migration.

Feature frontend tests cover definitions, dataset/preset/custom parameters, explicit computation, metadata, null versus zero, errors and actual API-row mapping into chart series. `features.spec.ts` signs in as USER, uses an already-seeded100-candle fixture (no import), checks EMA/RSI exact values, real canvas panes, UTC hover and desktop/tablet overflow. The REQ-003 Inspect selector is scoped to its dataset because coverage now has multiple datasets; its assertions are preserved. REQ-002 remains unchanged.

Local2026-09-19:87 backend PASS/4 skips (PostgreSQL opt-in and intentional SQLite concurrency skip);22 frontend PASS;3 E2E PASS; build/lint/typecheck PASS. CI35459280520:90 backend PASS/1 intentional SQLite concurrency skip,22 frontend PASS,3 E2E PASS; PostgreSQL snapshot regression and Docker PASS. Final-head evidence lives in REQ-004/PR #3.

Benchmark: `cd backend; python scripts/benchmark_features.py`:100,000 synthetic candles, STANDARD(EMA9/20/50,RSI14,ATR14,BB20/2),2.996seconds; Windows11 build26200, Intel64 Family6 Model151 Stepping2,20 logical CPUs, Python3.12.14. Single process, Decimal50, generation included, no SQL/JSON rendering. Development observation, not an SLA. Script prints current environment and timing on every run.

## REQ-003

Semantic human QA regression: `test_catalog_api_direction_contract_without_legacy_aliases` asserts the exact API field set (bullish/bearish/doji counts and probabilities, no legacy aliases), CCC=(6 samples,0 bullish,6 bearish,0 doji) with probabilities0/1/0, and CC=(12,6,6,0) with probabilities0.5/0.5/0. Engine, dataset/gap rules and database schema are unchanged. Frontend fixtures/types use the corrected direction fields.

`tests/test_req003.py` covers strict CSV/OHLC/Decimal/UTC validation, row/byte limits, ADMIN403/unauthenticated401, atomic rollback, exact duplicates, value conflicts, provenance/audit, pagination, all dataset dimensions, deterministic patterns2–5, gaps and doji exclusions. Explicit expected length3 counts for the 30-candle synthetic fixture are CCC=(6,0,6,0), CCP=(6,0,0,6), CPD/DCC/PDC=(4,4,0,0), with24 eligible and3 gap-skipped windows. These are fabricated observations, not market claims.

`tests/test_market_data_migration.py` checks001→002→003, legacy metadata normalization, ORM constraint/index alignment, safe downgrade and refusal of broker-less collisions. CI sets `CI_MARKET_DATA_POSTGRES_TESTS=true` against its disposable PostgreSQL service, also testing concurrent identical imports and exact NUMERIC precision in UUID-named test-owned schemas. PostgreSQL-only checks skip locally without explicit CI opt-in; SQLite is not evidence of PostgreSQL locking/precision.

Frontend marketData tests cover USER/ADMIN controls, confirmation/FormData upload, coverage, filters, detailed failure reports, empty states and API errors. E2E `market-data.spec.ts`: disposable ADMIN login → CSV fixture → coverage/report/inspection → cataloger length3 → CCC nextP6 and skipped gaps3, desktop/tablet screenshots. Existing REQ-002 browser scenario remains unchanged. All E2E data is temporary.

Benchmark: `cd backend; python scripts/benchmark_cataloger.py 100000`. Creates only a temporary synthetic SQLite database. Local2026-09-19:100,000 candles,6,560,041 CSV bytes, catalog0.9356s, ingestion7.7322s,99,997 eligible windows. This is a development measurement, not a production SLA or PostgreSQL performance claim.

Local suite at implementation checkpoint: 46 backend PASS/3 PostgreSQL-only or nonapplicable cases skipped; 18 frontend PASS; 2 E2E PASS. Remote CI 35456931568: 48 backend PASS/1 intentional SQLite concurrency skip; frontend/E2E and Docker PASS. PostgreSQL migration/concurrency tests run, not skipped. Final-head CI evidence is tracked in REQ-003 and PR #2. Full CI still runs PostgreSQL migrations/seed, backend, frontend/E2E and Docker build/startup.

REQ-002: `cd frontend; npm test` runs 10 formatter/component tests. `npx playwright install chromium` then `npx playwright test` starts disposable API/frontend servers (ports 8010/5174), seeds two accounts and validates login, selection, account-only start, over-risk rejection, WIN/LOSS net-risk summary, zero-result ledger invariance, limits, closure, journal reload and desktop/tablet overflow. Python must be on PATH or supplied as `CIBERQUANT_TEST_PYTHON`. The test API uses a temporary SQLite database and never accesses the user's trading data. CI additionally validates Alembic/seed against PostgreSQL and builds/starts Compose. Screenshots and failure traces are written to ignored `frontend/test-results/`.

Backend now includes 19 tests. `tests/test_financial_review.py` supplies isolated regression fixtures for the human financial review; `tests/test_finance.py` checks shared Decimal calculations, net-vs-gross capacity and stake caps. Tests deliberately cover rejected 20.01/20.18 stakes and valid 20.00/20.17 boundaries. Old max-loss testing with a 40 stake at 1% was replaced by valid successive losses of 20, 19.80 and 0.20.

Unit tests cover money formulas, risk limits and market-data quality. API/integration tests use an isolated SQLite test database only as a test harness; CI additionally applies Alembic to a clean PostgreSQL service before running them. Quant regression fixtures are deterministic and must be extended for cataloger/backtesting. Run `cd backend; python -m pytest` and frontend checks with `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
