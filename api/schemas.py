from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .models import SubStatus, CancelStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SubscriptionOut(BaseModel):
    id: int
    merchant: str
    plan: Optional[str]
    amount: float
    interval: str
    next_renewal_at: Optional[datetime]
    status: SubStatus
    class Config:
        from_attributes = True

class ApprovalIn(BaseModel):
    decision: str  # approve | deny

class CancellationOut(BaseModel):
    id: int
    subscription_id: int
    method: str
    status: CancelStatus
    class Config:
        from_attributes = True
