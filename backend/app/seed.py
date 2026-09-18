from passlib.context import CryptContext
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from .models import User
def main():
    with SessionLocal() as s:
        if not s.scalar(select(User).where(User.email==settings.seed_admin_email.lower())):
            s.add(User(email=settings.seed_admin_email.lower(),password_hash=CryptContext(schemes=['bcrypt']).hash(settings.seed_admin_password),name='CiberQuant Admin',role='ADMIN')); s.commit()
if __name__=='__main__': main()
