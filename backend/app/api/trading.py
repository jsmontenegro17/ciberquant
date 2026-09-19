from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from ..models import TradingAccount, TradingSession, Trade, LedgerEntry, JournalEntry, AuditLog, RiskProfile
from ..schemas import (
    AccountCreate,
    AccountOut,
    SessionStartRequest,
    SessionOut,
    TradeCreate,
    TradeOut,
    JournalCreate,
    JournalOut,
    LedgerOut,
    SessionSummary,
    AnalyticsOverview,
)
from ..services.finance import binary_profit, session_risk, session_net_pnl, stake_for_balance
from ..schemas import RiskPreview, SessionHistory
from .deps import db, current_user

router = APIRouter(tags=["trading"])


@router.get("/accounts/{account_id}/risk-preview", response_model=RiskPreview)
def risk_preview(account_id: int, user=Depends(current_user), s: Session = Depends(db)):
    account = s.scalar(select(TradingAccount).where(TradingAccount.id == account_id, TradingAccount.user_id == user.id))
    if not account:
        raise HTTPException(404, "Account not found")
    profile = s.scalar(select(RiskProfile).where(RiskProfile.user_id == user.id))
    if not profile:
        raise HTTPException(409, "No risk profile configured")
    return RiskPreview(
        trading_account_id=account.id,
        current_balance=account.current_balance,
        currency=account.currency,
        risk_per_trade_percent=profile.risk_per_trade_percent,
        suggested_stake=session_risk(
            account.current_balance,
            profile.risk_per_trade_percent,
            stake_for_balance(account.current_balance, profile.max_session_loss_percent),
            profile.max_session_operations,
            [],
        ).suggested_stake,
        max_loss_amount=stake_for_balance(account.current_balance, profile.max_session_loss_percent),
        max_operations=profile.max_session_operations,
        minimum_payout_percent=profile.minimum_payout_percent,
        profit_target_amount=stake_for_balance(account.current_balance, profile.profit_target_percent)
        if profile.profit_target_percent is not None
        else None,
    )


@router.post("/accounts", response_model=AccountOut)
def create_account(data: AccountCreate, user=Depends(current_user), s: Session = Depends(db)):
    a = TradingAccount(user_id=user.id, current_balance=data.initial_balance, **data.model_dump())
    s.add(a)
    s.flush()
    s.add(
        LedgerEntry(
            account_id=a.id,
            entry_type="INITIAL_BALANCE",
            amount=data.initial_balance,
            balance_before=Decimal("0"),
            balance_after=data.initial_balance,
        )
    )
    s.commit()
    s.refresh(a)
    return a


@router.get("/accounts", response_model=list[AccountOut])
def accounts(user=Depends(current_user), s: Session = Depends(db)):
    return s.scalars(select(TradingAccount).where(TradingAccount.user_id == user.id)).all()


@router.get("/accounts/{account_id}/ledger", response_model=list[LedgerOut])
def account_ledger(account_id: int, user=Depends(current_user), s: Session = Depends(db)):
    if not s.scalar(select(TradingAccount).where(TradingAccount.id == account_id, TradingAccount.user_id == user.id)):
        raise HTTPException(404, "Account not found")
    return s.scalars(select(LedgerEntry).where(LedgerEntry.account_id == account_id).order_by(LedgerEntry.created_at.desc())).all()


@router.post("/sessions", response_model=SessionOut)
def create_session(data: SessionStartRequest, user=Depends(current_user), s: Session = Depends(db)):
    a = s.scalar(
        select(TradingAccount).where(TradingAccount.id == data.trading_account_id, TradingAccount.user_id == user.id).with_for_update()
    )
    if not a:
        raise HTTPException(404, "Account not found")
    if a.status != "ACTIVE" or a.current_balance <= 0:
        raise HTTPException(409, "Account is not available for a session")
    profile = s.scalar(select(RiskProfile).where(RiskProfile.user_id == user.id))
    if not profile:
        raise HTTPException(409, "No risk profile configured")
    snapshot = {
        "risk_per_trade_percent": profile.risk_per_trade_percent,
        "max_loss_amount": stake_for_balance(a.current_balance, profile.max_session_loss_percent),
        "max_operations": profile.max_session_operations,
        "minimum_payout_percent": profile.minimum_payout_percent,
        "profit_target_amount": stake_for_balance(a.current_balance, profile.profit_target_percent)
        if profile.profit_target_percent is not None
        else None,
    }
    if s.scalar(
        select(TradingSession).where(
            TradingSession.trading_account_id == a.id, TradingSession.user_id == user.id, TradingSession.status == "OPEN"
        )
    ):
        raise HTTPException(409, "An active session already exists for this account")
    x = TradingSession(user_id=user.id, starting_balance=a.current_balance, **data.model_dump(), **snapshot)
    s.add(x)
    s.flush()
    s.add(AuditLog(user_id=user.id, event_type="SESSION_STARTED", entity_type="session", entity_id=x.id))
    s.commit()
    s.refresh(x)
    return x


@router.get("/sessions", response_model=list[SessionHistory])
def sessions(user=Depends(current_user), s: Session = Depends(db)):
    totals = (
        select(
            Trade.trading_session_id.label("sid"),
            func.count(Trade.id).label("total"),
            func.sum(case((Trade.result == "WIN", 1), else_=0)).label("wins"),
            func.sum(case((Trade.result == "LOSS", 1), else_=0)).label("losses"),
            func.sum(Trade.profit_loss).label("pnl"),
        )
        .where(Trade.user_id == user.id)
        .group_by(Trade.trading_session_id)
        .subquery()
    )
    rows = s.execute(
        select(TradingSession, TradingAccount.currency, totals.c.total, totals.c.wins, totals.c.losses, totals.c.pnl)
        .join(TradingAccount, TradingAccount.id == TradingSession.trading_account_id)
        .outerjoin(totals, totals.c.sid == TradingSession.id)
        .where(TradingSession.user_id == user.id)
        .order_by(TradingSession.started_at.desc())
    ).all()
    return [
        SessionHistory(
            **SessionOut.model_validate(sess).model_dump(),
            currency=currency,
            total_trades=total or 0,
            wins=wins or 0,
            losses=losses or 0,
            net_pnl=pnl or Decimal("0"),
            win_rate=Decimal(wins or 0) / Decimal((wins or 0) + (losses or 0)) * 100 if (wins or losses) else Decimal("0"),
        )
        for sess, currency, total, wins, losses, pnl in rows
    ]


@router.get("/sessions/{session_id}/trades", response_model=list[TradeOut])
def session_trades(session_id: int, user=Depends(current_user), s: Session = Depends(db)):
    if not s.scalar(select(TradingSession).where(TradingSession.id == session_id, TradingSession.user_id == user.id)):
        raise HTTPException(404, "Session not found")
    return s.scalars(select(Trade).where(Trade.trading_session_id == session_id).order_by(Trade.opened_at, Trade.id)).all()


@router.post("/sessions/{session_id}/close", response_model=SessionOut)
def close_session(session_id: int, user=Depends(current_user), s: Session = Depends(db)):
    sess = s.scalar(select(TradingSession).where(TradingSession.id == session_id, TradingSession.user_id == user.id).with_for_update())
    if not sess:
        raise HTTPException(404, "Session not found")
    if sess.status == "CLOSED":
        return sess
    account = s.scalar(select(TradingAccount).where(TradingAccount.id == sess.trading_account_id, TradingAccount.user_id == user.id))
    sess.status = "CLOSED"
    sess.ended_at = datetime.now(timezone.utc)
    sess.ending_balance = account.current_balance
    s.add(AuditLog(user_id=user.id, event_type="SESSION_CLOSED", entity_type="session", entity_id=sess.id))
    s.commit()
    s.refresh(sess)
    return sess


@router.post("/trades", response_model=TradeOut)
def create_trade(data: TradeCreate, user=Depends(current_user), s: Session = Depends(db)):
    sess = s.scalar(
        select(TradingSession).where(TradingSession.id == data.trading_session_id, TradingSession.user_id == user.id).with_for_update()
    )
    a = s.scalar(
        select(TradingAccount).where(TradingAccount.id == data.trading_account_id, TradingAccount.user_id == user.id).with_for_update()
    )
    if not a or not sess:
        raise HTTPException(404, "Account or session not found")
    if sess.trading_account_id != a.id:
        raise HTTPException(422, "Session does not belong to account")
    if sess.status != "OPEN":
        raise HTTPException(409, "Session is not open")
    trades = s.scalars(select(Trade).where(Trade.trading_session_id == sess.id)).all()
    risk = session_risk(
        a.current_balance, sess.risk_per_trade_percent, sess.max_loss_amount, sess.max_operations, (t.profit_loss for t in trades)
    )
    if risk.limit_reached:
        raise HTTPException(409, "SESSION LIMIT REACHED")
    if data.stake > risk.per_trade_max_stake:
        raise HTTPException(422, "Stake exceeds per-trade risk limit")
    if data.stake > risk.suggested_stake:
        raise HTTPException(422, "Stake exceeds balance or remaining session risk")
    if data.payout_percent < sess.minimum_payout_percent:
        raise HTTPException(422, "Payout is below session minimum")
    pl = binary_profit(data.stake, data.payout_percent, data.result) if data.result else None
    t = Trade(user_id=user.id, profit_loss=pl, **data.model_dump())
    s.add(t)
    s.flush()
    if pl is not None and pl != 0:
        before = a.current_balance
        after = before + pl
        a.current_balance = after
        s.add(
            LedgerEntry(
                account_id=a.id,
                trade_id=t.id,
                session_id=sess.id,
                entry_type="TRADE_PROFIT" if pl > 0 else "TRADE_LOSS",
                amount=pl,
                balance_before=before,
                balance_after=after,
            )
        )
    s.add(AuditLog(user_id=user.id, event_type="TRADE_CREATED", entity_type="trade", entity_id=t.id))
    s.commit()
    s.refresh(t)
    return t


@router.post("/journal", response_model=JournalOut)
def journal(data: JournalCreate, user=Depends(current_user), s: Session = Depends(db)):
    if data.session_id is not None and not s.scalar(
        select(TradingSession).where(TradingSession.id == data.session_id, TradingSession.user_id == user.id)
    ):
        raise HTTPException(404, "Session not found")
    if data.trade_id is not None:
        trade = s.scalar(select(Trade).where(Trade.id == data.trade_id, Trade.user_id == user.id))
        if not trade:
            raise HTTPException(404, "Trade not found")
        if data.session_id is not None and trade.trading_session_id != data.session_id:
            raise HTTPException(422, "Trade does not belong to session")
        data = data.model_copy(update={"session_id": trade.trading_session_id})
    x = JournalEntry(user_id=user.id, **data.model_dump())
    s.add(x)
    s.flush()
    s.add(AuditLog(user_id=user.id, event_type="JOURNAL_CREATED", entity_type="journal", entity_id=x.id))
    s.commit()
    s.refresh(x)
    return x


@router.get("/journal", response_model=list[JournalOut])
def journal_list(user=Depends(current_user), s: Session = Depends(db)):
    return s.scalars(select(JournalEntry).where(JournalEntry.user_id == user.id).order_by(JournalEntry.created_at.desc())).all()


def _summary(session_id: int, s: Session):
    trades = s.scalars(select(Trade).where(Trade.trading_session_id == session_id).order_by(Trade.opened_at, Trade.id)).all()
    sess = s.get(TradingSession, session_id)
    wins = sum(t.result == "WIN" for t in trades)
    losses = sum(t.result == "LOSS" for t in trades)
    draws = sum(t.result == "DRAW" for t in trades)
    cancelled = sum(t.result == "CANCELLED" for t in trades)
    pnl = [t.profit_loss or Decimal("0") for t in trades]
    max_win = max_loss = win = loss = 0
    for t in trades:
        if t.result == "WIN":
            win += 1
            loss = 0
        elif t.result == "LOSS":
            loss += 1
            win = 0
        else:
            win = loss = 0
        max_win = max(max_win, win)
        max_loss = max(max_loss, loss)
    net = session_net_pnl(pnl)
    gross_profit = sum((p for p in pnl if p > 0), Decimal("0"))
    gross_loss = sum((p for p in pnl if p < 0), Decimal("0"))
    account = s.get(TradingAccount, sess.trading_account_id)
    risk = session_risk(
        sess.ending_balance if sess.ending_balance is not None else account.current_balance,
        sess.risk_per_trade_percent,
        sess.max_loss_amount,
        sess.max_operations,
        pnl,
    )
    return SessionSummary(
        session_id=session_id,
        total_trades=len(trades),
        wins=wins,
        losses=losses,
        draws=draws,
        cancelled=cancelled,
        win_rate=(Decimal(wins) / Decimal(wins + losses) * Decimal("100") if wins + losses else Decimal("0")),
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_pnl=net,
        starting_balance=sess.starting_balance,
        ending_balance=sess.ending_balance if sess.ending_balance is not None else account.current_balance,
        max_win_streak=max_win,
        max_loss_streak=max_loss,
        currency=account.currency,
        suggested_stake=risk.suggested_stake,
        loss_consumed=risk.loss_consumed,
        remaining_risk=risk.remaining_risk,
        operations_remaining=max(0, sess.max_operations - len(trades)),
        limit_reached=risk.limit_reached,
        limit_reason=risk.limit_reason,
    )


@router.get("/sessions/{session_id}/summary", response_model=SessionSummary)
def session_summary(session_id: int, user=Depends(current_user), s: Session = Depends(db)):
    sess = s.scalar(select(TradingSession).where(TradingSession.id == session_id, TradingSession.user_id == user.id))
    if not sess:
        raise HTTPException(404, "Session not found")
    return _summary(session_id, s)


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def overview(account_id: int | None = None, user=Depends(current_user), s: Session = Depends(db)):
    q = select(TradingAccount).where(TradingAccount.user_id == user.id)
    account = s.scalar(q.where(TradingAccount.id == account_id)) if account_id else s.scalar(q.order_by(TradingAccount.id))
    if not account:
        raise HTTPException(404, "Account not found")
    trades = s.scalars(select(Trade).where(Trade.user_id == user.id, Trade.trading_account_id == account.id)).all()
    now = datetime.now(timezone.utc)
    day = now.date()
    month = now.month
    wins = sum(t.result == "WIN" for t in trades)
    resolved = sum(t.result in ("WIN", "LOSS") for t in trades)
    pnl = lambda xs: sum((t.profit_loss or Decimal("0") for t in xs), Decimal("0"))
    sessions = s.scalars(
        select(TradingSession).where(TradingSession.user_id == user.id, TradingSession.trading_account_id == account.id)
    ).all()
    active = next((x for x in sessions if x.status == "OPEN"), None)
    win = loss = max_win = max_loss = 0
    for trade in sorted(trades, key=lambda t: (t.opened_at, t.id)):
        if trade.result == "WIN":
            win += 1
            loss = 0
        elif trade.result == "LOSS":
            loss += 1
            win = 0
        else:
            win = loss = 0
        max_win = max(max_win, win)
        max_loss = max(max_loss, loss)
    return AnalyticsOverview(
        recent_trades=sorted(trades, key=lambda t: (t.opened_at, t.id), reverse=True)[:10],
        current_balance=account.current_balance,
        today_pnl=pnl([t for t in trades if t.opened_at.date() == day]),
        month_pnl=pnl([t for t in trades if t.opened_at.month == month and t.opened_at.year == now.year]),
        total_trades=len(trades),
        monthly_trades=sum(t.opened_at.month == month and t.opened_at.year == now.year for t in trades),
        win_rate=(Decimal(wins) / Decimal(resolved) * Decimal("100") if resolved else Decimal("0")),
        sessions_count=sum(x.started_at.month == month and x.started_at.year == now.year for x in sessions),
        current_session=active,
        max_win_streak=max_win,
        max_loss_streak=max_loss,
    )
