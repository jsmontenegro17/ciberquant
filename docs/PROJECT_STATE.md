# Project State

## Current version
0.5.0-dev on REQ-005 branch. Stable main/tag v0.4.0 at6a3a5bdf9beb69241807f48660f11117fdc55034.

## Functional
REQ-004 — DONE, Human Acceptance PASS on2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality, Candle Cataloger, Feature Engine, Indicator Engine and Feature Lab. Official engine cq-features-v1 is frozen; full-candle features are available at close_time only.
REQ-003 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality and Candle Cataloger. The accepted catalog contract describes bullish/bearish/doji candles, never binary trade results.
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
Behavioural analytics remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery. Import recovery/background ingestion is separate P2 debt DATA-001.

## Foundation only
Statistical validation remains future scope. Strategies and in-sample binary backtesting are implemented on the REQ-005 branch pending QA/acceptance; indicators and Feature Lab remain the accepted REQ-004 baseline.

## Planned
Validation/walk-forward, live data/scanning and integrated research workspace.

## Modules in development
REQ-005 — Strategy Lab & Binary Backtesting Engine: IN_PROGRESS. Private immutable versions, typed DSL, causal next-open execution, exact unit outcomes/metrics, snapshots/hashes, owned APIs and UI. IN-SAMPLE / NOT VALIDATED. REQ-001/002/003/004 remain DONE; cq-features-v1 source unchanged.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic001–003 stable;004_strategy_backtesting adds strategies, strategy_versions, backtest_runs, backtest_trades and constraints/indexes on the REQ-005 branch. PostgreSQL/JSONB target; SQLite local test harness. Raw candles and financial tables/contracts unchanged. Downgrade004 discards derived research evidence; export/backup first.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
[BACKTEST-001](debt/BACKTEST-001-stale-run-recovery.md): stale synchronous RUNNING recovery. [BACKTEST-002](debt/BACKTEST-002-execution-realism.md): payout history/latency/spread realism. Both P2, separate future scope. UI flat AND/OR editor; nested DSL supported through API, never silently flattened.
[QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md): future versioned exact acceleration; current origin calculation rejects requests beyond caps without approximation. No implementation in REQ-004. Frontend bundle size warning and dependency warnings remain P2.
REQ-003 P2: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md). Interrupted synchronous imports can remain PROCESSING; raw data stays protected, exact reimport is idempotent and batches remain visible. Not a v0.3.0 blocker; no recovery implementation in this release.
Final human acceptance PASS on 2026-09-19 verified all four financial corrections: hard per-trade risk cap, net session loss, no DRAW/CANCELLED ledger movements, and backend-only session start requiring RiskProfile. No functional P0/P1 remains within REQ-002. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. [SEC-001](debt/SEC-001-production-auth-configuration.md) records environment-aware cookie/CORS/HTTPS configuration required before production, not a REQ-002 blocker.

## Active requirements
[REQ-005](requirements/REQ-005-strategy-lab-binary-backtesting.md): IN_PROGRESS. No statistical validation, money management, automatic trading or strategy recommendation. REQ-001 through REQ-004: DONE.

## Next milestones
REQ-005 Strategy Lab & Binary Backtesting Engine.
REQ-006 Validation & Walk-Forward Engine.
REQ-007 Live Data & Scanner.
REQ-008 Integrated Research Workspace / v1.0.
Only REQ-005 is authorized. REQ-006 and later require independent authorization; no automatic merge.
