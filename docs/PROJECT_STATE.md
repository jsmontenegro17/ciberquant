# Project State

## Current version
0.2.0-dev

## Functional
Foundation plus REQ-002 frontend auth, account view, real dashboard overview, session start/workspace/close, trade recording, session summary, ledger view and journal UI are implemented on the feature branch. Backend health, authentication, accounts, auditable ledger, risk, sessions, trades, journal API and market-data providers remain functional.

## Partial
Frontend session trade history and journal are functional but remain intentionally compact; analytics overview does not yet expose behavioural metrics. Backend candle import endpoint remains partial.

## Foundation only
Cataloger, indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Feature-complete frontend screens, cataloger, indicators, strategies, validation and backtesting.

## Modules in development
REQ-002 — Session Manager & Trading Journal (IN_PROGRESS on feature branch); cataloger, indicators, strategies and backtesting contracts.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic initial migration; PostgreSQL; Docker Compose.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
P0: none known. P1: behavioural analytics and candle import are pending; feature branch requires CI/QA before merge. P2: full quant engines remain next milestones.

## Active requirements
REQ-002 — Session Manager & Trading Journal (IN_PROGRESS).

## Next milestones
After REQ-002 is merged: REQ-003 cataloger; REQ-004 backtesting.
