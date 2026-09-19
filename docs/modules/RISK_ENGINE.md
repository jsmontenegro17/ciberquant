# Risk Engine
Purpose: stake and session guardrails. Services: `services/finance.py`; formulas include stake, payout, break-even, EV and session limit. Backend is source of truth. Martingale and auto-trading are out of scope.

REQ-002 adds typed account risk preview and session capacity fields. Frontend displays API values, and session creation requires a RiskProfile and snapshots it using the locked account balance. No client-provided financial settings are accepted. The user-scoped RiskProfile is reused; a profile editor and account-specific profile assignments are not introduced.

Human review corrections centralize risk in `services/finance.py`: net P&L is the sum of realized trade P&L; loss consumed is `max(0, -net_pnl)`; remaining risk is `max(0, max_loss_amount - loss_consumed)`. The absolute session floor is starting balance minus max loss. Gains increase the mathematical distance to that floor, but the specified remaining-risk formula caps spendable capacity at max_loss_amount while net P&L is positive. Profits never increase the per-trade percentage.

Per-trade maximum uses current balance × snapshotted risk percentage with centralized Decimal HALF_UP cent rounding. Suggested/allowed stake is the minimum of that maximum, remaining risk and available balance. The endpoint rejects a stake above the per-trade maximum with 422 `Stake exceeds per-trade risk limit`; exceeding another cap also returns 422. No overrides. Session stop uses net P&L <= -max_loss_amount or the operations limit. DRAW and CANCELLED both count as recorded operations/attempts.
