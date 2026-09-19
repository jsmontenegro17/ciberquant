# Project State

## Current version
0.3.0-dev (feature branch); stable main/tag remains v0.2.0.

## Functional
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
REQ-003 market data ingestion and deterministic candle cataloger are implemented on the feature branch, CI validated and in QA pending human acceptance. Behavioural analytics remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery.

## Foundation only
Indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Indicators, strategies, validation and backtesting.

## Modules in development
REQ-003 — Market Data Ingestion & Candle Cataloger: QA on codex/req-003-market-data-cataloger, [PR #2](https://github.com/jsmontenegro17/ciberquant/pull/2). Backend/PostgreSQL, frontend/E2E and Docker PASS. REQ-002 remains DONE, integrated in PR #1.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic 001 + 002 + 003 (broker-aware candle identity and import provenance on feature branch); PostgreSQL; Docker Compose. New admin CSV import, coverage/history/inspection and descriptive catalog APIs. Existing financial contracts unchanged.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
Final human acceptance PASS on 2026-09-19 verified all four financial corrections: hard per-trade risk cap, net session loss, no DRAW/CANCELLED ledger movements, and backend-only session start requiring RiskProfile. No functional P0/P1 remains within REQ-002. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. [SEC-001](debt/SEC-001-production-auth-configuration.md) records environment-aware cookie/CORS/HTTPS configuration required before production, not a REQ-002 blocker.

## Active requirements
REQ-003: QA, Human Acceptance PENDING. Implementation CI 35456931568 at c117822487802b42544f01b28d29123a61aab04d PASS; final-head checks in PR #2. REQ-001/REQ-002: DONE. New quant behavior is descriptive only, not strategy recommendations. No merge until separate human acceptance.

## Next milestones
Finish REQ-003 QA and human acceptance. REQ-004 Strategy Lab & Backtesting requires a separate authorization and is not started.
