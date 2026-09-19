# Analytics
Purpose: aggregate account and session overview. API `/api/v1/analytics/overview?account_id=...` and `/api/v1/sessions/{id}/summary`; ownership enforced. Current metrics cover balance, today/month P&L, trades, sessions and win rate. Behavioural analytics remain future scope.

REQ-002 includes recent trades and actual maximum win/loss streaks. UTC day/month boundaries use trade opening timestamps; `sessions_count` denotes sessions started in the current UTC month. Win rate excludes DRAW/CANCELLED from the denominator, while total trades counts every recorded operation. Streaks are ordered by opening time and ID, and reset on DRAW/CANCELLED. Currency is taken from the selected account; accounts are never aggregated across currencies.
