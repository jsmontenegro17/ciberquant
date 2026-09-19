from passlib.context import CryptContext
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from decimal import Decimal
from .models import User, TradingAccount, LedgerEntry, RiskProfile
def main():
    with SessionLocal() as s:
        user = s.scalar(select(User).where(User.email==settings.seed_admin_email.lower()))
        if not user:
            user=User(email=settings.seed_admin_email.lower(),password_hash=CryptContext(schemes=['bcrypt']).hash(settings.seed_admin_password),name='CiberQuant Admin',role='ADMIN'); s.add(user); s.flush()
        account=s.scalar(select(TradingAccount).where(TradingAccount.user_id==user.id,TradingAccount.name=='CiberQuant Demo Account'))
        if not account:
            account=TradingAccount(user_id=user.id,name='CiberQuant Demo Account',broker='Demo',currency='USD',initial_balance=Decimal('2000.00'),current_balance=Decimal('2000.00')); s.add(account); s.flush(); s.add(LedgerEntry(account_id=account.id,entry_type='INITIAL_BALANCE',amount=Decimal('2000.00'),balance_before=Decimal('0'),balance_after=Decimal('2000.00')))
        if not s.scalar(select(RiskProfile).where(RiskProfile.user_id==user.id)):
            s.add(RiskProfile(user_id=user.id,risk_per_trade_percent=Decimal('1.00'),max_session_loss_percent=Decimal('2.00'),max_session_operations=4,minimum_payout_percent=Decimal('80.00'),profit_target_percent=None))
        s.commit()
if __name__=='__main__': main()
