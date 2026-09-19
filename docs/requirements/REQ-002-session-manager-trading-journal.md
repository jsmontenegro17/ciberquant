# REQ-002 — Session Manager & Trading Journal

Status: IN_PROGRESS  
Priority: P1  
Classification: LARGE  
Created: 2026-09-19  
Updated: 2026-09-19

## Problem
La Foundation tiene API funcional, pero el frontend es un shell estático y no permite operar el flujo real de sesión, trades y journal.

## Objective
Conectar una aplicación frontend real a auth, cuentas, sesiones, trades, ledger, analytics y journal, manteniendo el backend como autoridad financiera.

## Scope
Frontend architecture, protected routing, dashboard/account/session workspace, session summaries, analytics overview, journal UX, API integration and regression tests.

## Out of Scope
Cataloger, backtesting, indicators, scanner, broker integrations, auto-trading, martingale and ML.

## User Stories
- Como trader, quiero iniciar sesión y trabajar con una cuenta real del backend.
- Como trader, quiero abrir, operar y cerrar una sesión viendo riesgo, P&L y límites.
- Como trader, quiero consultar y escribir notas relacionadas con sesiones/trades.

## Functional Requirements
Real login/logout/current user; protected routes; account selector; session creation/closure; trade recording; ledger/balance refresh; session summary/history; dashboard overview; journal CRUD/list.

## Non-functional Requirements
No financial hardcoding; credentials include; no JWT storage; Decimal calculations remain backend-owned; responsive desktop/tablet; accessible forms; query invalidation after mutations.

## Business Rules
Only one OPEN session per trading account. Closed sessions reject trades. User ownership applies to every resource. Risk and stake values displayed by UI come from backend snapshots.

## Acceptance Criteria
See source request sections 70 and 69. Final evidence must cover backend, frontend, integration, CI, Docker, security and manual user-flow QA.

## Affected Modules
Auth, trading accounts, risk, sessions, trades, journal, analytics, frontend app shell.

## Expected Files
`backend/app/api/`, `backend/app/schemas.py`, `backend/alembic/versions/`, `frontend/src/`, module docs and CI tests.

## Database Impact
Add session minimum payout snapshot and any minimal indexes/constraints required for session ownership/lifecycle.

## API Impact
Add typed session summary, analytics overview, account ledger and journal list/create contracts.

## Frontend Impact
Replace static shell with React Router, TanStack Query API client, protected layouts and functional session/trade/journal screens.

## Security Impact
HttpOnly cookie with credentials include, protected routes, centralized 401 handling and ownership tests.

## Financial Impact
Frontend previews are informational. Backend remains authority for stake, P&L, balance and ledger.

## Test Plan
Backend summary/analytics/ownership/lifecycle tests; frontend auth/session/trade/limits/close/journal tests; CI integration workflow.

## Migration Plan
Alembic migration from current head; CI validates from empty PostgreSQL.

## Rollback Plan
Downgrade the REQ-002 migration in non-production; revert feature branch before merge if necessary.

## Documentation Updates
Module docs, context index/manifest if paths change, PROJECT_STATE, CHANGELOG and this requirement.

## Implementation Notes
Start from `main` on `codex/req-002-session-manager-journal`; no changes to `main` directly.

## QA Evidence
Pending implementation.

## Final Result
Pending.
