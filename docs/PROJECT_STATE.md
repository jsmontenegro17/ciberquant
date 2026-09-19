# Project State

## Current version
0.2.0

## Functional
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
Behavioural analytics and the candle import endpoint remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery.

## Foundation only
Cataloger, indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Cataloger, indicators, strategies, validation and backtesting.

## Modules in development
None. REQ-002 — Session Manager & Trading Journal is DONE; delivery is tracked in [PR #1](https://github.com/jsmontenegro17/ciberquant/pull/1). REQ-003 has not started.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic 001 + 002 (session minimum payout snapshot); PostgreSQL; Docker Compose. Typed risk preview, summaries, ledger, journal and account overview contracts.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
Final human acceptance PASS on 2026-09-19 verified all four financial corrections: hard per-trade risk cap, net session loss, no DRAW/CANCELLED ledger movements, and backend-only session start requiring RiskProfile. No functional P0/P1 remains within REQ-002. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. [SEC-001](debt/SEC-001-production-auth-configuration.md) records environment-aware cookie/CORS/HTTPS configuration required before production, not a REQ-002 blocker.

## Active requirements
None. REQ-002 — Session Manager & Trading Journal: DONE, Human Acceptance PASS. Financial correction evidence remains in the requirement; final release-head CI and integration are tracked in PR #1 and main CI.

## Next milestones
Future, separately authorized requirements: REQ-003 cataloger; REQ-004 backtesting. Neither is initiated by the REQ-002 closure.
