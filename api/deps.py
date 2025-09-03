from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
import os

security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

class UserIdentity:
    def __init__(self, email: str):
        self.email = email

def get_current_user(creds = Depends(security)) -> UserIdentity:
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return UserIdentity(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
