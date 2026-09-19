from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from ..features.serialization import CALC_CONTEXT


@dataclass(frozen=True)
class BinaryOutcome:
    direction: str
    entry_time: datetime
    entry_price: Decimal
    expiry_time: datetime
    expiry_price: Decimal
    result: str
    unit_pnl: Decimal


def resolve(direction, entry_time, entry_price, expiry_time, expiry_price, payout):
    if direction not in ("CALL", "PUT") or expiry_time <= entry_time:
        raise ValueError("Invalid binary outcome direction/time")
    if not all(isinstance(v, Decimal) and v.is_finite() for v in (entry_price, expiry_price, payout)):
        raise ValueError("Outcome requires finite Decimals")
    if min(entry_price, expiry_price) <= 0 or not 0 < payout <= 100:
        raise ValueError("Invalid price/payout")
    result = "DRAW" if expiry_price == entry_price else "WIN" if (expiry_price > entry_price) == (direction == "CALL") else "LOSS"
    with localcontext(CALC_CONTEXT):
        pnl = payout / 100 if result == "WIN" else Decimal(-1) if result == "LOSS" else Decimal(0)
    return BinaryOutcome(direction, entry_time, entry_price, expiry_time, expiry_price, result, pnl)
