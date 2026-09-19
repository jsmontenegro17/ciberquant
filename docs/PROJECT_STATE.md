# Project State

## Current version
0.1.0

## Functional
Health endpoints, authentication, accounts, auditable ledger, session lifecycle, trades, risk calculations, journal API, market-data provider interface, Mock/CSV providers and data-quality checks.

## Partial
Frontend dashboard is a navigational shell with static overview data; it is not connected to the API. Backend aggregate session analytics and candle import endpoint remain partial.

## Foundation only
Cataloger, indicators, strategies, validation and backtesting have documentation/contracts but no production implementation.

## Planned
Feature-complete frontend screens, cataloger, indicators, strategies, validation and backtesting.

## Modules in development
Frontend feature screens; cataloger, indicators, strategies and backtesting contracts.

## Experimental / disabled
Auto-trading, broker integrations, ML and live streaming are disabled.

## Migrations / integrations
Alembic initial migration; PostgreSQL; Docker Compose.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
P0: none known. P1: frontend is a shell; candle import and aggregate session analytics are pending. P2: full quant engines remain next milestones.

## Active requirements
None. REQ-001 — Foundation is DONE after remote CI run `35415290649`.

## Next milestones
REQ-002 session UI and richer analytics; REQ-003 cataloger; REQ-004 backtesting. Do not start them until `main` is established from the final validated REQ-001 commit.
