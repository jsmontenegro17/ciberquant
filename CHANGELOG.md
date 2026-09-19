# Changelog

## [0.1.0] - 2026-09-18
### Added
- Foundation operativa, API FastAPI, PostgreSQL/Alembic, auth, accounts, ledger, sessions, trades, journal y market-data providers.
- Frontend React shell, Docker, CI, testing y documentación de contexto.

### Security
- Passwords hasheados y tokens JWT en cookies HttpOnly.

### QA
- Remote CI run 35415290649 validated backend, PostgreSQL migrations, idempotent seed, tests, frontend and Docker.

## [0.2.0] - Unreleased
### Added
- REQ-002 frontend API client, protected routes, account dashboard, session workspace, trade recording and journal workflow.
- Session summary, analytics overview, account ledger and session trade endpoints.
- Backend-authoritative risk preview, session capacity, account selection, filtered history/journal, and recent trades.
- Component workflow tests and real API Chromium QA at desktop/tablet widths, included in CI.
### Fixed
- Cross-account trade references and cross-user journal links are rejected.
- Serialized PostgreSQL financial writes; fresh risk snapshot on session start and authoritative balance refresh.
- Reproducible frontend Docker dependencies, API environment variable and Compose startup smoke checks.
