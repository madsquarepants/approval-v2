from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from ..db import get_db, SessionLocal
from ..models import CancellationRequest, Subscription, CancelStatus, SubStatus, User
from ..schemas import CancellationOut
from ..deps import get_current_user
from ..utils.log import log_event

router = APIRouter(prefix="/cancellations", tags=["cancellations"])

async def _delayed_complete(request_id: int, subscription_id: int, ok: bool = True, delay: float = 2.0):
    """Runs in background: wait, mark request complete, flip subscription, and log."""
    await asyncio.sleep(delay)
    db = SessionLocal()
    try:
        req = db.query(CancellationRequest).filter_by(id=request_id).first()
        sub = db.query(Subscription).filter_by(id=subscription_id).first()
        if not req:
            return
        req.status = CancelStatus.succeeded if ok else CancelStatus.failed
        req.completed_at = datetime.utcnow()
        if ok and sub:
            sub.status = SubStatus.canceled
        db.commit()
        if sub:
            log_event(db, sub.user_id, "cancel.done", f"Canceled {sub.merchant}", {"subscription_id": sub.id, "request_id": request_id})
            db.commit()
    finally:
        db.close()

@router.post("/{subscription_id}", response_model=CancellationOut)
def start_cancel(
    subscription_id: int,
    method: str = "assisted",
    db: Session = Depends(get_db),
    me = Depends(get_current_user),
    background: BackgroundTasks = None,
):
    sub = db.query(Subscription).filter_by(id=subscription_id).first()
    if not sub:
        raise HTTPException(404, "Not found")

    req = CancellationRequest(subscription_id=sub.id, method=method, status=CancelStatus.in_progress)
    db.add(req); db.commit(); db.refresh(req)

    user = db.query(User).filter_by(email=me.email).first()
    log_event(db, user.id, "cancel.start", f"Started cancellation for {sub.merchant}", {"subscription_id": sub.id, "request_id": req.id})
    db.commit()

    if background is not None:
        background.add_task(_delayed_complete, req.id, sub.id, True, 2.0)

    return req

@router.post("/{request_id}/complete", response_model=CancellationOut)
def complete_cancel(request_id: int, ok: bool = True, db: Session = Depends(get_db), me = Depends(get_current_user)):
    req = db.query(CancellationRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Not found")
    req.status = CancelStatus.succeeded if ok else CancelStatus.failed
    req.completed_at = datetime.utcnow()

    sub = db.query(Subscription).filter_by(id=req.subscription_id).first()
    if ok and sub:
        sub.status = SubStatus.canceled

    if sub:
        log_event(db, sub.user_id, "cancel.done", f"Canceled {sub.merchant}", {"subscription_id": sub.id, "request_id": req.id})
    db.commit(); db.refresh(req)
    return req
