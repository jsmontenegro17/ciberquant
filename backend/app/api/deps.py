from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from ..config import settings
from ..db import get_db
from ..models import User
def db(): yield from get_db()
def current_user(request:Request, session:Session=Depends(db)):
    token=request.cookies.get('access_token')
    if not token: raise HTTPException(401,'Authentication required')
    try: uid=jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])['sub']
    except (JWTError,KeyError): raise HTTPException(401,'Invalid authentication')
    user=session.get(User,int(uid))
    if not user or user.status != 'ACTIVE': raise HTTPException(401,'Inactive user')
    return user

def require_admin(user=Depends(current_user)):
    if user.role != 'ADMIN': raise HTTPException(403, 'Administrator role required')
    return user
