# Changelog

## [0.3.0] - 2026-09-19
### Acceptance
- REQ-003 DONE; Human Acceptance PASS includes final semantic contract correction. Candle direction is not binary trade outcome.
- DATA-001 records import recovery as separate P2 debt, not a release blocker; no recovery implementation added.
### Fixed
- Human semantic QA: catalog statistics use bullish/bearish candle-direction fields without legacy aliases; distinguish candle color from future binary trade outcomes. Mathematical results unchanged.
### Added
- REQ-003 broker-aware immutable candle identity, import provenance and migration 003.
- ADMIN-only atomic CSV ingestion with UTC/Decimal validation, limits, duplicate/conflict handling and audit events.
- Paginated dataset coverage, import history and candle inspection; backend timeframe options.
- Deterministic C/P/D cataloger for lengths 2–5, gap/doji exclusion and descriptive next-candle distributions.
- Connected Market Data/Cataloger UI, synthetic fixtures, backend/frontend/E2E and PostgreSQL concurrency/migration regressions.
### Boundaries
- No trading recommendations, strategies, indicators, backtesting or live integration. Human acceptance completed PASS; REQ-004 not started.

## [0.1.0] - 2026-09-18
### Added
- Foundation operativa, API FastAPI, PostgreSQL/Alembic, auth, accounts, ledger, sessions, trades, journal y market-data providers.
- Frontend React shell, Docker, CI, testing y documentación de contexto.

### Security
- Passwords hasheados y tokens JWT en cookies HttpOnly.

### QA
- Remote CI run 35415290649 validated backend, PostgreSQL migrations, idempotent seed, tests, frontend and Docker.

## [0.2.0] - 2026-09-19
### Acceptance
- REQ-002 DONE; final Human Acceptance PASS verifies all four financial QA findings. No functional P0/P1 remains in scope.
- Production cookie/CORS/HTTPS configuration is tracked as SEC-001 future security debt, not a blocker for local development.
### Added
- REQ-002 frontend API client, protected routes, account dashboard, session workspace, trade recording and journal workflow.
- Session summary, analytics overview, account ledger and session trade endpoints.
- Backend-authoritative risk preview, session capacity, account selection, filtered history/journal, and recent trades.
- Component workflow tests and real API Chromium QA at desktop/tablet widths, included in CI.
### Fixed
- REQ-002 human financial review: enforce per-trade percentage; calculate session capacity from net P&L; avoid zero-value DRAW/CANCELLED ledger entries; accept account-only session start and require backend RiskProfile.
- Cross-account trade references and cross-user journal links are rejected.
- Serialized PostgreSQL financial writes; fresh risk snapshot on session start and authoritative balance refresh.
- Reproducible frontend Docker dependencies, API environment variable and Compose startup smoke checks.
