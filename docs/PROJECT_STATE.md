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
REQ-001 is the bootstrap exception. After CI validation, `main` must be created from the final REQ-001 SHA. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
P0: backend/Docker execution evidence depends on CI because the current host has no Python or Docker; GitHub Actions currently reports no workflow runs. An administrator must enable Actions if repository settings require it, run CI manually, then create `main` from the validated SHA. P1: frontend is a shell; candle import and aggregate session analytics are pending. P2: full quant engines remain next milestones.

## Active requirements
REQ-001 — Foundation (QA).

## Next milestones
REQ-002 session UI and richer analytics; REQ-003 cataloger; REQ-004 backtesting.
