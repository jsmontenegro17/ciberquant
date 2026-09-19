# Sessions
Purpose: snapshot and constrain a trading session. Table: `trading_sessions`; API `/api/v1/sessions`, `/api/v1/sessions/{id}/close`, `/api/v1/sessions/{id}/summary` and `/api/v1/sessions/{id}/trades`. Rules: OPEN/CLOSED/STOPPED, max loss/operations/payout checked before a trade, one OPEN session per account, close is idempotent and audited. Summary exposes W/L/D, P&L, win rate and streaks.

REQ-002: account rows serialize session starts and session rows serialize trades/closure on PostgreSQL. Configured risk settings are read again at start and frozen on the session; later profile changes do not change that snapshot. The risk profile remains user-scoped (Foundation model), applied to each selected account's balance.

`GET /accounts/{id}/risk-preview` returns the current balance, currency, suggested stake, risk %, maximum loss/operations, minimum payout and optional target. Summary additionally returns loss consumed, remaining risk, remaining operations and an explicit limit reason. Loss capacity is cumulative gross losses, not net P&L. Recommended stake uses current account balance and snapshotted risk percentage. Closed summaries preserve ending balance including zero.

Session history includes W/L, trade count, win rate and net P&L via a single grouped query. Frontend account/status/date filters operate on the fetched user-scoped list. Detail includes trade timestamps, summary, guardrails and associated journal notes; closure requires confirmation and disables trade entry after reload.
