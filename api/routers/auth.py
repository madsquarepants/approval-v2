from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import User
from ..schemas import UserCreate, Token
from ..utils.security import hash_password, verify_password, create_token

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(400, "Email already registered")
    u = User(email=payload.email, pw_hash=hash_password(payload.password))
    db.add(u); db.commit()
    token = create_token(u.email)
    return {"access_token": token}

@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=payload.email).first()
    if not u or not verify_password(payload.password, u.pw_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(u.email)}
