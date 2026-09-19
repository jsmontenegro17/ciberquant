# Sessions
Purpose: snapshot and constrain a trading session. Table: `trading_sessions`; API `/api/v1/sessions` and `/api/v1/sessions/{id}/close`. Rules: OPEN/CLOSED/STOPPED, max loss and max operations checked before a trade; close is idempotent and audited. Aggregate metrics pending.
