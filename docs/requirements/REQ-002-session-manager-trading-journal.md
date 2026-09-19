# REQ-002 — Session Manager & Trading Journal

Status: QA
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
Real login/logout/current user; protected routes; account selector; session creation/closure; trade recording; ledger/balance refresh; session summary/history; dashboard overview; journal create/list.

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

### Human Review Financial Corrections
Status: QA; corrections implemented, no merge authorized. No database migration needed.

| Problem | Correction | Regression / result |
|---|---|---|
| P0: per-trade risk was advisory | Centralized Decimal per-trade maximum enforced with 422 | 20.00 accepted / 20.01 rejected at 2000; after WIN, 20.17 accepted / 20.18 rejected. PASS |
| P0: session loss used gross losing trades | Shared Risk Engine computes net P&L, nonnegative consumed loss and remaining risk | 2000 + 16.80 - 20.17 = 1996.63; consumed 3.37; remaining 36.63. Floor reached via valid stakes 20, 19.80, 0.20; 0.21 rejected at final step. PASS |
| P1: zero-result trades created TRADE_LOSS ledger rows | Persist trade/audit but no monetary entry for zero P&L | DRAW and CANCELLED preserve balance, leave ledger unchanged, each counts toward max_operations. PASS |
| P1: client controlled risk when profile missing | SessionStartRequest contains only account ID and optional notes; backend requires profile and freezes snapshot | Missing profile: 409; arbitrary fields: 422; profile changes do not alter existing snapshots; OpenAPI and frontend payload assertions. PASS |

Local validation: backend 19 tests, frontend 10 tests, lint/typecheck/build and real API browser workflow PASS. Browser also verifies over-risk rejection, the net-risk summary and unchanged ledger after DRAW/CANCELLED. Existing ownership tests retained.

Correction CI: [35454718064](https://github.com/jsmontenegro17/ciberquant/actions/runs/35454718064), commit `8f22c626f55a115c8ed48e5055388c06bc6f7680` — Backend PASS, Frontend/E2E PASS, Docker build/startup PASS. PR #1 remains open in QA; final documentation-only head checks are linked from its description. All four findings are covered by passing regressions. Final human acceptance is still required; no merge performed.

Decisions: retain negative `gross_loss` for contract compatibility. `suggested_stake` is capped by all three limits. The session floor remains starting_balance - max_loss_amount; following the requested formula, positive net P&L does not expand spendable remaining risk above max_loss_amount, although it increases mathematical distance to the floor. Neither risk overrides nor profile editing are introduced.

### Historical QA before financial review
The following evidence predates the findings; it is retained for traceability and does not validate the corrected financial semantics.
2026-09-19: Backend 11 tests PASS; frontend 8 tests PASS; lint/typecheck/build PASS. Chromium against FastAPI with a disposable SQLite database validates account selection, backend stake, WIN/LOSS, balance update, max-operations blocking, closure/reload and session journal persistence. Desktop 1366×768 and tablet 768×1024 were checked; screenshots inspected locally with no page overflow.

Integration evidence: starting balance 2000; WIN stake 20 at 84% = +16.80; next recommended stake 20.17; LOSS = -20.17; ending balance 1996.63. Ledger, summary, W/L, closure and isolation verified. Separate tests cover max-loss rejection, invalid market/stake, DRAW/CANCELLED, cross-account references and cross-user journal links.

CI [35453839696](https://github.com/jsmontenegro17/ciberquant/actions/runs/35453839696), commit `337cd370f1ff323b4310545b2330a56a6453828a`: Backend PASS, Frontend including E2E PASS, Docker build + Compose startup PASS. This run validates PostgreSQL migration/seed and startup. Browser business-flow tests use SQLite; they do not claim PostgreSQL concurrency coverage. Final documentation/version/additional-test commit must also pass PR checks.

### Acceptance results
- PASS: real login, logout, persistent HttpOnly authentication and protected routes.
- PASS: account selection and API dashboard; no static financial results in product screens.
- PASS: start session, workspace, backend risk/stake and real trade recording.
- PASS: balance/P&L refresh, auditable ledger and operation/loss limits.
- PASS: confirmed closure, closed-state persistence, history and complete summary.
- PASS: journal creation, session/trade ownership, filters and reload persistence.
- PASS: backend/frontend tests, browser scenarios A–D and API isolation scenario E.
- PASS: CI and Docker build/startup at the linked validated commit.
- PASS: documentation and [PR #1](https://github.com/jsmontenegro17/ciberquant/pull/1).
- Pending human review: final acceptance before DONE/merge. No tag/release created.

### Implementation boundaries
Risk profiles remain user-scoped; account selection changes balance/currency and the resulting calculations. History/journal filters are client-side over user-owned API lists. Behavioural engines, market import and REQ-003 were not implemented. Development cookies are not represented as production deployment hardening. P0/P1 defects: none known in validated scope. P2: dependency deprecation warnings and future pagination.

## Final Result
Implemented on `codex/req-002-session-manager-journal`, PR #1, prepared version `0.2.0-dev`; awaiting final human QA and merge. REQ-003 must wait until REQ-002 is DONE and separately authorized.
