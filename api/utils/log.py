import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import EventLog

def log_event(db: Session, user_id: int, type_: str, message: str, payload: Optional[Dict[str, Any]] = None):
    """
    Lightweight event logger.
    Usage: log_event(db, user_id, "approval.decide", "DENY Netflix", {"subscription_id": 123})
    """
    ev = EventLog(user_id=user_id, type=type_, message=message, payload=json.dumps(payload or {}))
    db.add(ev)  # commit happens in the calling router
