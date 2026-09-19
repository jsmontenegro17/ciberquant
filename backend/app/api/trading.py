from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import TradingAccount,TradingSession,Trade,LedgerEntry,JournalEntry,AuditLog
from ..schemas import AccountCreate,AccountOut,SessionCreate,SessionOut,TradeCreate,TradeOut,JournalCreate,JournalOut
from ..services.finance import binary_profit,session_limit_reached
from .deps import db,current_user
router=APIRouter(tags=['trading'])
@router.post('/accounts',response_model=AccountOut)
def create_account(data:AccountCreate,user=Depends(current_user),s:Session=Depends(db)):
    a=TradingAccount(user_id=user.id,current_balance=data.initial_balance,**data.model_dump()); s.add(a); s.flush(); s.add(LedgerEntry(account_id=a.id,entry_type='INITIAL_BALANCE',amount=data.initial_balance,balance_before=Decimal('0'),balance_after=data.initial_balance)); s.commit(); s.refresh(a); return a
@router.get('/accounts',response_model=list[AccountOut])
def accounts(user=Depends(current_user),s:Session=Depends(db)): return s.scalars(select(TradingAccount).where(TradingAccount.user_id==user.id)).all()
@router.post('/sessions',response_model=SessionOut)
def create_session(data:SessionCreate,user=Depends(current_user),s:Session=Depends(db)):
    a=s.scalar(select(TradingAccount).where(TradingAccount.id==data.trading_account_id,TradingAccount.user_id==user.id))
    if not a: raise HTTPException(404,'Account not found')
    x=TradingSession(user_id=user.id,starting_balance=a.current_balance,**data.model_dump()); s.add(x); s.flush(); s.add(AuditLog(user_id=user.id,event_type='SESSION_STARTED',entity_type='session',entity_id=x.id)); s.commit(); s.refresh(x); return x
@router.get('/sessions',response_model=list[SessionOut])
def sessions(user=Depends(current_user),s:Session=Depends(db)): return s.scalars(select(TradingSession).where(TradingSession.user_id==user.id)).all()
@router.post('/sessions/{session_id}/close',response_model=SessionOut)
def close_session(session_id:int,user=Depends(current_user),s:Session=Depends(db)):
    sess=s.scalar(select(TradingSession).where(TradingSession.id==session_id,TradingSession.user_id==user.id))
    if not sess: raise HTTPException(404,'Session not found')
    if sess.status=='CLOSED': return sess
    account=s.scalar(select(TradingAccount).where(TradingAccount.id==sess.trading_account_id,TradingAccount.user_id==user.id))
    sess.status='CLOSED'; sess.ended_at=datetime.now(timezone.utc); sess.ending_balance=account.current_balance
    s.add(AuditLog(user_id=user.id,event_type='SESSION_CLOSED',entity_type='session',entity_id=sess.id)); s.commit(); s.refresh(sess); return sess
@router.post('/trades',response_model=TradeOut)
def create_trade(data:TradeCreate,user=Depends(current_user),s:Session=Depends(db)):
    a=s.scalar(select(TradingAccount).where(TradingAccount.id==data.trading_account_id,TradingAccount.user_id==user.id)); sess=s.scalar(select(TradingSession).where(TradingSession.id==data.trading_session_id,TradingSession.user_id==user.id))
    if not a or not sess: raise HTTPException(404,'Account or session not found')
    if sess.status!='OPEN': raise HTTPException(409,'Session is not open')
    trades=s.scalars(select(Trade).where(Trade.trading_session_id==sess.id)).all(); ops=len(trades); loss=sum((-t.profit_loss for t in trades if t.profit_loss and t.profit_loss<0),Decimal('0'))
    if session_limit_reached(loss,sess.max_loss_amount,ops,sess.max_operations): raise HTTPException(409,'SESSION LIMIT REACHED')
    pl=binary_profit(data.stake,data.payout_percent,data.result) if data.result else None
    t=Trade(user_id=user.id,profit_loss=pl,**data.model_dump()); s.add(t); s.flush()
    if pl is not None:
        before=a.current_balance; after=before+pl; a.current_balance=after; s.add(LedgerEntry(account_id=a.id,trade_id=t.id,session_id=sess.id,entry_type='TRADE_PROFIT' if pl>0 else 'TRADE_LOSS',amount=pl,balance_before=before,balance_after=after))
    s.add(AuditLog(user_id=user.id,event_type='TRADE_CREATED',entity_type='trade',entity_id=t.id)); s.commit(); s.refresh(t); return t
@router.post('/journal',response_model=JournalOut)
def journal(data:JournalCreate,user=Depends(current_user),s:Session=Depends(db)):
    x=JournalEntry(user_id=user.id,**data.model_dump()); s.add(x); s.flush(); s.add(AuditLog(user_id=user.id,event_type='JOURNAL_CREATED',entity_type='journal',entity_id=x.id)); s.commit(); s.refresh(x); return x
