from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; email:str; name:str; role:str; status:str
class Login(BaseModel): email:str; password:str
class AccountCreate(BaseModel): name:str; broker:str|None=None; currency:str='USD'; initial_balance:Decimal=Field(gt=0)
class AccountOut(AccountCreate): model_config=ConfigDict(from_attributes=True); id:int; current_balance:Decimal; status:str
class SessionCreate(BaseModel): trading_account_id:int; risk_per_trade_percent:Decimal=Field(gt=0,le=100); max_loss_amount:Decimal=Field(gt=0); max_operations:int=Field(gt=0); profit_target_amount:Decimal|None=None; notes:str|None=None
class SessionOut(SessionCreate): model_config=ConfigDict(from_attributes=True); id:int; user_id:int; starting_balance:Decimal; status:str; started_at:datetime
class TradeCreate(BaseModel): trading_account_id:int; trading_session_id:int; symbol:str; market_type:str; timeframe:str; direction:str; stake:Decimal=Field(gt=0); payout_percent:Decimal=Field(ge=0,le=100); result:str|None=None; notes:str|None=None
class TradeOut(TradeCreate): model_config=ConfigDict(from_attributes=True); id:int; profit_loss:Decimal|None
class JournalCreate(BaseModel): title:str; content:str; trade_id:int|None=None; session_id:int|None=None
class JournalOut(JournalCreate): model_config=ConfigDict(from_attributes=True); id:int; user_id:int; created_at:datetime
