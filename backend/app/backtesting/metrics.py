from decimal import Decimal, localcontext
from ..features.serialization import CALC_CONTEXT


def summarize(trades, payout, counters):
    with localcontext(CALC_CONTEXT):
        wins = losses = draws = ws = ls = maxw = maxl = 0
        equity = peak = drawdown = profit = loss = Decimal(0)
        curve = [{"sequence_no": 0, "equity": Decimal(0), "time": None}]
        for i, t in enumerate(trades, 1):
            result, pnl = t["result"], t["unit_pnl"]
            wins += result == "WIN"
            losses += result == "LOSS"
            draws += result == "DRAW"
            ws = ws + 1 if result == "WIN" else 0
            ls = ls + 1 if result == "LOSS" else 0
            maxw, maxl = max(maxw, ws), max(maxl, ls)
            profit += max(pnl, Decimal(0))
            loss += max(-pnl, Decimal(0))
            equity += pnl
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
            curve.append({"sequence_no": i, "equity": equity, "time": t["expiry_time"]})
        resolved = wins + losses
        rate = Decimal(wins) * 100 / resolved if resolved else None
        breakeven = 100 / (1 + payout / 100)
        return {
            **counters,
            "trades_executed": len(trades),
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "resolved_trades": resolved,
            "win_rate_percent": rate,
            "break_even_win_rate_percent": breakeven,
            "edge_percentage_points": rate - breakeven if rate is not None else None,
            "ev_per_resolved_trade": (wins * payout / 100 - losses) / resolved if resolved else None,
            "average_pnl_per_signal": equity / len(trades) if trades else None,
            "total_unit_pnl": equity,
            "gross_profit_units": profit,
            "gross_loss_units": loss,
            "profit_factor": profit / loss if loss else None,
            "max_win_streak": maxw,
            "max_loss_streak": maxl,
            "max_drawdown_units": drawdown,
        }, curve
