# REQ-001 — CiberQuant Foundation

Status: QA  
Priority: CRITICAL  
Created: 2026-09-18  
Updated: 2026-09-18

## Problem
El repositorio estaba vacío y no tenía base funcional ni memoria operacional.

## Objective
Crear una base multiusuario, auditable y ejecutable para continuar el desarrollo cuantitativo.

## Scope
Operating system del repositorio; FastAPI; PostgreSQL/Alembic; auth/users; accounts/ledger; risk/sessions/trades/journal; market-data mock/CSV/data quality; frontend shell; Docker/CI/tests.

## Out of Scope
Auto-trading, broker APIs, indicadores avanzados, cataloger UI y backtesting completo.

## Business Rules
Money uses Decimal/NUMERIC. Payout is stored per trade. Session limits are checked before new trades. User ownership is mandatory. Regular and OTC are separate.

## User Stories
- Como usuario, quiero iniciar sesión y ver sólo mis datos financieros.
- Como trader, quiero registrar cuenta, sesión, operación y nota con balance auditable.
- Como investigador, quiero consumir velas deterministas sin auto-trading.

## Functional Requirements
- API versionada con health/readiness, auth, accounts, sessions, trades y journal.
- Ledger inicial y P&L calculado en backend.
- Proveedores Mock/CSV y validación OHLC.

## Non-functional Requirements
UTC, multiusuario, configuración por entorno, migraciones explícitas, reproducibilidad y CI.

## Acceptance Criteria
- Backend, frontend y PostgreSQL tienen configuración reproducible.
- Auth, account, ledger, session, trade, risk y market-data foundation tienen contratos y tests.
- Migrations, seed, CI, docs y branch están preparados.

## Affected Modules
Auth, users, trading accounts, risk, sessions, trades, journal, market data, platform docs.

## Expected Files
`backend/`, `frontend/`, `docs/`, `.github/`, `docker-compose.yml`.

## Database Impact
Initial Alembic migration creates users, accounts, ledger, sessions, trades, journal entries and candles.

## API Impact
Adds `/health`, `/ready` and `/api/v1/auth`, `/accounts`, `/sessions`, `/trades`, `/journal`.

## Frontend Impact
Adds responsive research dashboard shell and navigation for future feature areas.

## Security Impact
Password hashes, HttpOnly JWT cookie and user ownership filters; production cookie hardening remains deployment-specific.

## Financial Impact
Decimal/NUMERIC, payout-specific binary P&L and immutable ledger evidence.

## Test Plan
Backend pytest; deterministic service tests; frontend lint/typecheck/build; Docker smoke checks.

## Migration Plan
`alembic upgrade head`; rollback via `alembic downgrade base` in non-production environments.

## Documentation Updates
AGENTS, context index/manifest, module docs, state, runbook, testing, ADRs and changelog.

## Implementation Notes
SQLite is only a local/test fallback; production configuration is PostgreSQL. Broker adapters and order execution are deliberately absent.

## QA Evidence

| Command / check | Environment | Result | Observation |
|---|---|---|---|
| `npm ci` | Windows host | PASS | Clean dependency install |
| `npm run lint` | Windows host | PASS | ESLint completed without errors |
| `npm run typecheck` | Windows host | PASS | TypeScript completed without errors |
| `npm test` | Windows host | PASS | Typecheck-backed frontend smoke command |
| `npm run build` | Windows host | PASS | Vite production build generated |
| `python -m pytest` | Windows host | UNVERIFIED | Python is unavailable on this host |
| `alembic upgrade head` | Windows host | UNVERIFIED | Requires Python and PostgreSQL |
| `docker compose build/up` | Windows host | UNVERIFIED | Docker is unavailable on this host |
| GitHub CI workflow | Remote | UNVERIFIED | Branch was pushed; GitHub Actions currently reports 0 workflow runs |

Fixes applied during QA: reproducible seed account/risk profile, audit log, idempotent session close, duplicate-candle validation, integration tests, PostgreSQL migration job and Docker CI job. Commit evidence is recorded in Git.

## Final Result
Foundation QA corrections implemented. Status remains QA because backend, migration, seed, PostgreSQL and Docker evidence is still UNVERIFIED in the available environment.
