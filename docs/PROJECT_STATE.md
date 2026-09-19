# Project State

## Current version
0.3.0

## Functional
REQ-003 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality and Candle Cataloger. The accepted catalog contract describes bullish/bearish/doji candles, never binary trade results.
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
Behavioural analytics remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery. Import recovery/background ingestion is separate P2 debt DATA-001.

## Foundation only
Indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Indicators, strategies, validation and backtesting.

## Modules in development
None. REQ-003 — Market Data Ingestion & Candle Cataloger: DONE, Human Acceptance PASS; release delivery tracked in [PR #2](https://github.com/jsmontenegro17/ciberquant/pull/2). REQ-002 remains DONE, integrated in PR #1.

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
None. REQ-001/REQ-002/REQ-003: DONE. Human Acceptance PASS includes the semantic correction at b460d3ed9fc21011fff44398b6c202aa0f1f276f. Release/main CI and tag evidence are linked from REQ-003. No trading recommendations or binary outcome engine implemented.

## Next milestones
REQ-004 Strategy Lab & Backtesting requires a separate authorization and is not started.
