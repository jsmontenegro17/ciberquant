# Trading Accounts
Purpose: cuentas y balance auditable. Tables: `trading_accounts`, `account_ledger_entries`. Money uses NUMERIC/Decimal. API: `/api/v1/accounts`. Invariant: every initial balance creates ledger entry; current_balance is a projection.
