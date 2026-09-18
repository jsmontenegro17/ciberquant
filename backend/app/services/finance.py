from decimal import Decimal, ROUND_HALF_UP
def money(value: Decimal) -> Decimal: return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
def stake_for_balance(balance: Decimal, risk_percent: Decimal) -> Decimal: return money(balance * risk_percent / Decimal('100'))
def binary_profit(stake: Decimal, payout_percent: Decimal, result: str) -> Decimal:
    if result == 'WIN': return money(stake * payout_percent / Decimal('100'))
    if result == 'LOSS': return money(-stake)
    if result in ('DRAW','CANCELLED'): return Decimal('0.00')
    raise ValueError('Unsupported trade result')
def break_even(payout_percent: Decimal) -> Decimal:
    if payout_percent <= 0: raise ValueError('payout must be positive')
    return Decimal('100') / (Decimal('100') + payout_percent)
def expected_value(win_rate: Decimal, payout_percent: Decimal) -> Decimal:
    return (win_rate * payout_percent / Decimal('100')) - (Decimal('1') - win_rate)
def session_limit_reached(loss: Decimal, max_loss: Decimal, operations: int, max_operations: int) -> bool:
    return loss >= max_loss or operations >= max_operations
