from decimal import Decimal
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.main import app
from app.api.deps import db
from app.models import User, TradingAccount, TradingSession, Trade, LedgerEntry, AuditLog

engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine)
Base.metadata.create_all(engine)
def override_db():
    with TestingSession() as session: yield session
app.dependency_overrides[db]=override_db
client=TestClient(app)
def setup_user(email):
    with TestingSession() as s:
        user=User(email=email,password_hash=CryptContext(schemes=['bcrypt']).hash('secret'),name=email); s.add(user); s.commit()
def login(email):
    response=client.post('/api/v1/auth/login',json={'email':email,'password':'secret'}); assert response.status_code==200; return response
def test_auth_and_ownership():
    setup_user('a@example.com'); setup_user('b@example.com')
    assert client.get('/api/v1/auth/me').status_code==401
    login('a@example.com'); created=client.post('/api/v1/accounts',json={'name':'A','initial_balance':'2000.00'}); assert created.status_code==200
    login('b@example.com'); assert client.get('/api/v1/accounts').json()==[]
def test_ledger_session_close_and_idempotency():
    setup_user('c@example.com'); login('c@example.com')
    account=client.post('/api/v1/accounts',json={'name':'C','initial_balance':'2000.00'}).json()
    session=client.post('/api/v1/sessions',json={'trading_account_id':account['id'],'risk_per_trade_percent':'1','max_loss_amount':'40','max_operations':4}).json()
    trade=client.post('/api/v1/trades',json={'trading_account_id':account['id'],'trading_session_id':session['id'],'symbol':'EURUSD','market_type':'REGULAR','timeframe':'1m','direction':'CALL','stake':'20','payout_percent':'84','result':'WIN'}).json()
    assert trade['profit_loss']=='16.80'
    closed=client.post(f"/api/v1/sessions/{session['id']}/close"); assert closed.status_code==200 and closed.json()['status']=='CLOSED'
    assert client.post(f"/api/v1/sessions/{session['id']}/close").status_code==200
    assert client.post('/api/v1/trades',json={'trading_account_id':account['id'],'trading_session_id':session['id'],'symbol':'EURUSD','market_type':'REGULAR','timeframe':'1m','direction':'CALL','stake':'20','payout_percent':'84','result':'LOSS'}).status_code==409
    with TestingSession() as s:
        account_row=s.scalar(select(TradingAccount).where(TradingAccount.name=='C'))
        assert account_row.current_balance==Decimal('2016.80')
        assert len(s.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_row.id)).all())==2
        assert s.scalar(select(AuditLog).where(AuditLog.event_type=='SESSION_CLOSED')) is not None
