# Testing

## REQ-003

`tests/test_req003.py` covers strict CSV/OHLC/Decimal/UTC validation, row/byte limits, ADMIN403/unauthenticated401, atomic rollback, exact duplicates, value conflicts, provenance/audit, pagination, all dataset dimensions, deterministic patterns2–5, gaps and doji exclusions. Explicit expected length3 counts for the 30-candle synthetic fixture are CCC=(6,0,6,0), CCP=(6,0,0,6), CPD/DCC/PDC=(4,4,0,0), with24 eligible and3 gap-skipped windows. These are fabricated observations, not market claims.

`tests/test_market_data_migration.py` checks001→002→003, legacy metadata normalization, ORM constraint/index alignment, safe downgrade and refusal of broker-less collisions. CI sets `CI_MARKET_DATA_POSTGRES_TESTS=true` against its disposable PostgreSQL service, also testing concurrent identical imports and exact NUMERIC precision in UUID-named test-owned schemas. PostgreSQL-only checks skip locally without explicit CI opt-in; SQLite is not evidence of PostgreSQL locking/precision.

Frontend marketData tests cover USER/ADMIN controls, confirmation/FormData upload, coverage, filters, detailed failure reports, empty states and API errors. E2E `market-data.spec.ts`: disposable ADMIN login → CSV fixture → coverage/report/inspection → cataloger length3 → CCC nextP6 and skipped gaps3, desktop/tablet screenshots. Existing REQ-002 browser scenario remains unchanged. All E2E data is temporary.

Benchmark: `cd backend; python scripts/benchmark_cataloger.py 100000`. Creates only a temporary synthetic SQLite database. Local2026-09-19:100,000 candles,6,560,041 CSV bytes, catalog0.9356s, ingestion7.7322s,99,997 eligible windows. This is a development measurement, not a production SLA or PostgreSQL performance claim.

Local suite at implementation checkpoint: 46 backend PASS/3 PostgreSQL-only or nonapplicable cases skipped; 18 frontend PASS; 2 E2E PASS. Remote CI 35456931568: 48 backend PASS/1 intentional SQLite concurrency skip; frontend/E2E and Docker PASS. PostgreSQL migration/concurrency tests run, not skipped. Final-head CI evidence is tracked in REQ-003 and PR #2. Full CI still runs PostgreSQL migrations/seed, backend, frontend/E2E and Docker build/startup.

REQ-002: `cd frontend; npm test` runs 10 formatter/component tests. `npx playwright install chromium` then `npx playwright test` starts disposable API/frontend servers (ports 8010/5174), seeds two accounts and validates login, selection, account-only start, over-risk rejection, WIN/LOSS net-risk summary, zero-result ledger invariance, limits, closure, journal reload and desktop/tablet overflow. Python must be on PATH or supplied as `CIBERQUANT_TEST_PYTHON`. The test API uses a temporary SQLite database and never accesses the user's trading data. CI additionally validates Alembic/seed against PostgreSQL and builds/starts Compose. Screenshots and failure traces are written to ignored `frontend/test-results/`.

Backend now includes 19 tests. `tests/test_financial_review.py` supplies isolated regression fixtures for the human financial review; `tests/test_finance.py` checks shared Decimal calculations, net-vs-gross capacity and stake caps. Tests deliberately cover rejected 20.01/20.18 stakes and valid 20.00/20.17 boundaries. Old max-loss testing with a 40 stake at 1% was replaced by valid successive losses of 20, 19.80 and 0.20.

Unit tests cover money formulas, risk limits and market-data quality. API/integration tests use an isolated SQLite test database only as a test harness; CI additionally applies Alembic to a clean PostgreSQL service before running them. Quant regression fixtures are deterministic and must be extended for cataloger/backtesting. Run `cd backend; python -m pytest` and frontend checks with `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
