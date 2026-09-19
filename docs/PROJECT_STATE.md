# Project State

## Current version
0.4.0-dev on REQ-004 branch; stable main/tag v0.3.0.

## Functional
REQ-003 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality and Candle Cataloger. The accepted catalog contract describes bullish/bearish/doji candles, never binary trade results.
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
Behavioural analytics remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery. Import recovery/background ingestion is separate P2 debt DATA-001.

## Foundation only
Strategies, validation and backtesting remain future contracts. REQ-004 now implements indicators on its feature branch, not stable main.

## Planned
Strategies, validation, backtesting and live scanning.

## Modules in development
REQ-004 — Feature & Indicator Engine: IN_PROGRESS. Pure cq-features-v1, reproducible snapshot APIs and Feature Lab. No schema change or new migration. REQ-003 remains DONE / Human Acceptance PASS in PR #2; REQ-002 remains DONE in PR #1.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic 001 + 002 + 003 (broker-aware candle identity and import provenance); PostgreSQL; Docker Compose. Admin CSV import, coverage/history/inspection and descriptive catalog APIs. Existing financial contracts unchanged.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
REQ-003 P2: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md). Interrupted synchronous imports can remain PROCESSING; raw data stays protected, exact reimport is idempotent and batches remain visible. Not a v0.3.0 blocker; no recovery implementation in this release.
Final human acceptance PASS on 2026-09-19 verified all four financial corrections: hard per-trade risk cap, net session loss, no DRAW/CANCELLED ledger movements, and backend-only session start requiring RiskProfile. No functional P0/P1 remains within REQ-002. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. [SEC-001](debt/SEC-001-production-auth-configuration.md) records environment-aware cookie/CORS/HTTPS configuration required before production, not a REQ-002 blocker.

## Active requirements
[REQ-004](requirements/REQ-004-feature-indicator-engine.md): IN_PROGRESS, human acceptance pending. REQ-001/REQ-002/REQ-003: DONE. No strategies, trading recommendations, binary outcome engine or backtesting implemented.

## Next milestones
REQ-004 Feature & Indicator Engine (IN_PROGRESS).
REQ-005 Strategy Lab & Binary Backtesting Engine.
REQ-006 Validation & Walk-Forward Engine.
REQ-007 Live Data & Scanner.
REQ-008 Integrated Research Workspace / v1.0.
Only REQ-004 is authorized; subsequent requirements are not started.
