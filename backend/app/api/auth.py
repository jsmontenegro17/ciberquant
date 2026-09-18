from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import settings
from ..models import User
from ..schemas import Login, UserOut
from .deps import db, current_user
router=APIRouter(prefix='/auth',tags=['auth']); pwd=CryptContext(schemes=['bcrypt'],deprecated='auto')
@router.post('/login',response_model=UserOut)
def login(data:Login,response:Response,session:Session=Depends(db)):
    user=session.scalar(select(User).where(User.email==data.email.lower()))
    if not user or not pwd.verify(data.password,user.password_hash): raise HTTPException(401,'Invalid credentials')
    token=jwt.encode({'sub':str(user.id),'exp':datetime.now(timezone.utc)+timedelta(hours=8)},settings.jwt_secret,algorithm='HS256')
    response.set_cookie('access_token',token,httponly=True,samesite='lax',secure=False,max_age=28800)
    return user
@router.post('/logout')
def logout(response:Response):
    response.delete_cookie('access_token')
    return {'ok':True}
@router.get('/me',response_model=UserOut)
def me(user=Depends(current_user)): return user
