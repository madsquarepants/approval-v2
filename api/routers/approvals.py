# api/routers/approvals.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import SessionLocal
from ..utils.auth import get_current_user
from ..utils.log import log_event

router = APIRouter(prefix="/approvals", tags=["approvals"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
async def decide(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Accepts: { "subscription_id": number, "decision": "approve" | "deny" }
    Records the decision and logs an event.
    (If you have an approvals table, you can upsert into it; for MVP we just log.)
    """
    sub_id = payload.get("subscription_id")
    decision = (payload.get("decision") or "").lower().strip()

    if not sub_id:
        raise HTTPException(400, "subscription_id is required")
    if decision not in {"approve", "deny"}:
        raise HTTPException(400, "decision must be 'approve' or 'deny'")

    # ensure subscription exists
    row = db.execute(text("SELECT id FROM subscriptions WHERE id = :id"), {"id": sub_id}).mappings().first()
    if not row:
        raise HTTPException(404, "subscription not found")

    # (optional) if you have an approvals table, upsert here
    # try:
    #     db.execute(text("""
    #         INSERT INTO approvals (subscription_id, user_id, decision)
    #         VALUES (:sid, :uid, :dec)
    #         ON CONFLICT (subscription_id) DO UPDATE SET decision = :dec
    #     """), {"sid": sub_id, "uid": user.id, "dec": decision})
    # except Exception:
    #     pass

    # log event
    log_event(db, user.id, f"approval.{decision}", f"{decision} sub {sub_id}", {"subscription_id": sub_id})
    db.commit()

    return {"subscription_id": sub_id, "decision": decision}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import SessionLocal
from ..utils.auth import get_current_user
from ..utils.log import log_event

router = APIRouter(prefix="/approvals", tags=["approvals"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
async def decide(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Body: { subscription_id, decision: 'approve' | 'deny' }
    - Records decision
    - If 'deny', automatically starts cancellation (same as POST /cancellations/start)
    """
    sub_id = payload.get("subscription_id")
    decision = (payload.get("decision") or "").lower().strip()

    if not sub_id:
        raise HTTPException(400, "subscription_id is required")
    if decision not in {"approve", "deny"}:
        raise HTTPException(400, "decision must be 'approve' or 'deny'")

    row = db.execute(text("SELECT id FROM subscriptions WHERE id = :id"), {"id": sub_id}).mappings().first()
    if not row:
        raise HTTPException(404, "subscription not found")

    # log decision
    log_event(db, user.id, f"approval.{decision}", f"{decision} sub {sub_id}", {"subscription_id": sub_id})
    db.commit()

    started = False
    start_error = None
    if decision == "deny":
        # lazy import to avoid circular imports
        try:
            from .cancellations import start_cancellation as _start_cancel
            # reuse the same handler (keeps state = in_progress)
            await _start_cancel({"subscription_id": sub_id}, user=user, db=db)
            started = True
        except Exception as e:
            start_error = str(e)
            log_event(db, user.id, "cancel.autostart_failed", start_error, {"subscription_id": sub_id})
            db.commit()

    return {
        "subscription_id": sub_id,
        "decision": decision,
        "cancel_started": started,
        "error": start_error,
    }

