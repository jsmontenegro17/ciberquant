# Project State

## Current version
0.2.0-dev

## Functional
Foundation plus REQ-002 frontend auth, account view, real dashboard overview, session start/workspace/close, trade recording, session summary, ledger view and journal UI are implemented on the feature branch. Backend health, authentication, accounts, auditable ledger, risk, sessions, trades, journal API and market-data providers remain functional.

## Partial
Behavioural analytics and the candle import endpoint remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery.

## Foundation only
Cataloger, indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Cataloger, indicators, strategies, validation and backtesting.

## Modules in development
REQ-002 — Session Manager & Trading Journal is in QA on its feature branch and [PR #1](https://github.com/jsmontenegro17/ciberquant/pull/1). Backend/frontend tests, browser E2E and Compose startup passed. No merge or release yet.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic 001 + 002 (session minimum payout snapshot); PostgreSQL; Docker Compose. Typed risk preview, summaries, ledger, journal and account overview contracts.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
Human review found two P0 and two P1 financial issues, corrected on the REQ-002 branch: hard per-trade risk cap, net session loss, no zero-result ledger movements, and backend-only session start requiring RiskProfile. Local financial regressions pass; final human acceptance remains pending. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. Development cookie settings remain local-only; production hardening is not claimed.

## Active requirements
REQ-002 — Session Manager & Trading Journal (QA). Human financial corrections validated by CI run 35454718064 at commit 8f22c626f55a115c8ed48e5055388c06bc6f7680 (backend, frontend/E2E, Docker build/startup PASS). Detailed findings/tests/results in the requirement's Human Review Financial Corrections section; final head checks and acceptance in PR #1.

## Next milestones
After REQ-002 is merged: REQ-003 cataloger; REQ-004 backtesting.
