from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Iterable


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def stake_for_balance(balance: Decimal, risk_percent: Decimal) -> Decimal:
    return money(balance * risk_percent / Decimal("100"))


def binary_profit(stake: Decimal, payout_percent: Decimal, result: str) -> Decimal:
    if result == "WIN":
        return money(stake * payout_percent / Decimal("100"))
    if result == "LOSS":
        return money(-stake)
    if result in ("DRAW", "CANCELLED"):
        return Decimal("0.00")
    raise ValueError("Unsupported trade result")


def break_even(payout_percent: Decimal) -> Decimal:
    if payout_percent <= 0:
        raise ValueError("payout must be positive")
    return Decimal("100") / (Decimal("100") + payout_percent)


def expected_value(win_rate: Decimal, payout_percent: Decimal) -> Decimal:
    return (win_rate * payout_percent / Decimal("100")) - (Decimal("1") - win_rate)


def session_limit_reached(loss: Decimal, max_loss: Decimal, operations: int, max_operations: int) -> bool:
    return loss >= max_loss or operations >= max_operations


def session_net_pnl(realized: Iterable[Decimal | None]) -> Decimal:
    return sum((p if p is not None else Decimal("0") for p in realized), Decimal("0"))


def session_loss_consumed(net_pnl: Decimal) -> Decimal:
    return max(Decimal("0"), -net_pnl)


def session_remaining_loss(net_pnl: Decimal, max_loss: Decimal) -> Decimal:
    # Spendable risk is capped at the configured budget, even after profits.
    return max(Decimal("0"), max_loss - session_loss_consumed(net_pnl))


def max_trade_stake(balance: Decimal, risk_percent: Decimal, remaining: Decimal) -> Decimal:
    return max(Decimal("0"), min(stake_for_balance(balance, risk_percent), remaining, balance))


@dataclass(frozen=True)
class SessionRisk:
    net_pnl: Decimal
    loss_consumed: Decimal
    remaining_risk: Decimal
    per_trade_max_stake: Decimal
    suggested_stake: Decimal
    limit_reason: str | None

    @property
    def limit_reached(self) -> bool:
        return self.limit_reason is not None


def session_risk(
    balance: Decimal, risk_percent: Decimal, max_loss: Decimal, max_operations: int, realized: Iterable[Decimal | None]
) -> SessionRisk:
    results = list(realized)
    net = session_net_pnl(results)
    consumed = session_loss_consumed(net)
    remaining = session_remaining_loss(net, max_loss)
    reason = None
    if session_limit_reached(consumed, max_loss, len(results), max_operations):
        reason = "Maximum session loss reached" if net <= -max_loss else "Maximum operations reached"
    return SessionRisk(
        net, consumed, remaining, stake_for_balance(balance, risk_percent), max_trade_stake(balance, risk_percent, remaining), reason
    )
