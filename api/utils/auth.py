from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from ..db import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _cred_exc():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

class CurrentUser:
    def __init__(self, uid: int, email: str | None = None):
        self.id = uid
        self.email = email

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        raise _cred_exc()
    sub = payload.get("sub")
    uid = payload.get("user_id")
    email = payload.get("email")
    row = None
    if isinstance(uid, int):
        row = db.execute(text("SELECT id, email FROM users WHERE id=:id"), {"id": uid}).mappings().first()
    elif sub is not None:
        if isinstance(sub, int) or (isinstance(sub, str) and sub.isdigit()):
            row = db.execute(text("SELECT id, email FROM users WHERE id=:id"), {"id": int(sub)}).mappings().first()
        else:
            row = db.execute(text("SELECT id, email FROM users WHERE email=:email"), {"email": sub}).mappings().first()
    elif email:
        row = db.execute(text("SELECT id, email FROM users WHERE email=:email"), {"email": email}).mappings().first()
    if not row:
        raise _cred_exc()
    return CurrentUser(uid=row["id"], email=row.get("email"))
