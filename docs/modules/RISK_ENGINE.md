# Risk Engine
Purpose: stake and session guardrails. Services: `services/finance.py`; formulas include stake, payout, break-even, EV and session limit. Backend is source of truth. Martingale and auto-trading are out of scope.

REQ-002 adds typed account risk preview and session capacity fields. Frontend displays API values, and session creation re-reads configured settings and locked account balance. Trades cannot exceed available account balance or remaining cumulative session loss capacity. The user-scoped RiskProfile is reused; a profile editor and account-specific profile assignments are not introduced.
