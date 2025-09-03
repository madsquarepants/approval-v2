from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..deps import get_current_user
from ..models import EventLog, User



Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/")
def list_events(limit: int = 50, db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    rows = (db.query(EventLog)
            .filter_by(user_id=user.id)
            .order_by(EventLog.id.desc())
            .limit(limit).all())
    return [{"id": r.id, "type": r.type, "message": r.message, "created_at": r.created_at.isoformat()} for r in rows]
