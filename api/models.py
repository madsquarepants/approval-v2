from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base
import enum

class SubStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    canceling = "canceling"
    canceled = "canceled"

class CancelStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    succeeded = "succeeded"
    failed = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    pw_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscriptions = relationship("Subscription", back_populates="user")

class InstitutionConnection(Base):
    __tablename__ = "institution_connections"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    provider = Column(String)  # e.g., plaid
    status = Column(String, default="linked")
    access_token_ref = Column(String)  # store a reference only

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    merchant = Column(String, index=True)
    plan = Column(String)
    amount = Column(Float)
    interval = Column(String)  # monthly, yearly
    next_renewal_at = Column(DateTime, nullable=True)
    status = Column(Enum(SubStatus), default=SubStatus.active)
    user = relationship("User", back_populates="subscriptions")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    subscription_id = Column(Integer, index=True)
    decision = Column(String)  # approve | deny
    decided_at = Column(DateTime, default=datetime.utcnow)

class CancellationRequest(Base):
    __tablename__ = "cancellation_requests"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, index=True)
    method = Column(String)  # auto|assisted
    status = Column(Enum(CancelStatus), default=CancelStatus.pending)
    vendor_ref = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

from sqlalchemy import Text
from datetime import datetime

class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    type = Column(String, index=True)          # e.g., approval.decide, cancel.start, cancel.done, scan.real
    message = Column(String)                    # short human text
    payload = Column(Text, nullable=True)       # optional JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

