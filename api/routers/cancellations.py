# api/routers/cancellations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import SessionLocal
from ..utils.auth import get_current_user
from ..utils.log import log_event

router = APIRouter(prefix="/cancellations", tags=["cancellations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/start")
async def start_cancellation(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Step 1 behavior:
    - Immediately set cancel_status='in_progress'
    - Fire the adapter (stubbed success here; plug in email adapter later)
    - Keep 'in_progress' (verification job flips it to 'canceled' later)
    - If adapter fails, set 'failed'
    """
    sub_id = payload.get("subscription_id")
    if not sub_id:
        raise HTTPException(400, "subscription_id is required")

    # ensure subscription exists (and belongs to user if you enforce that)
    sub = db.execute(text("SELECT id FROM subscriptions WHERE id=:id"), {"id": sub_id}).mappings().first()
    if not sub:
        raise HTTPException(404, "subscription not found")

    # put the subscription into in_progress immediately
    db.execute(text(
        "UPDATE subscriptions SET cancel_status='in_progress' WHERE id=:id"
    ), {"id": sub_id})
    db.commit()

    log_event(db, user.id, "cancel.start", f"Starting cancellation for sub {sub_id}", {"subscription_id": sub_id})

    # ----- call your real adapter here (email/portal). For step 1, stub success. -----
    try:
        # result = await run_email_adapter(db, user, <full subscription row>)
        result = {"ok": True}  # stub: success

        if result.get("ok"):
            log_event(db, user.id, "cancel.queued", "Adapter sent; awaiting verification",
                      {"subscription_id": sub_id})
            # stay in 'in_progress' for verification step
            return {"subscription_id": sub_id, "status": "in_progress"}
        else:
            raise RuntimeError(result.get("error") or "adapter failed")

    except Exception as e:
        db.execute(text(
            "UPDATE subscriptions SET cancel_status='failed' WHERE id=:id"
        ), {"id": sub_id})
        db.commit()
        log_event(db, user.id, "cancel.failed", str(e), {"subscription_id": sub_id})
        raise HTTPException(500, f"Cancellation failed: {e}")

@router.get("/status/{subscription_id}")
def get_cancellation_status(subscription_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id, cancel_status, canceled_at FROM subscriptions WHERE id=:id"
    ), {"id": subscription_id}).mappings().first()
    if not row:
        raise HTTPException(404, "not found")
    return {"subscription_id": row["id"], "cancel_status": row["cancel_status"], "canceled_at": row["canceled_at"]}
