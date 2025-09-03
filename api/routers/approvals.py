from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Subscription, Approval, SubStatus, User
from ..schemas import ApprovalIn, SubscriptionOut
from ..deps import get_current_user
from ..utils.log import log_event

router = APIRouter(prefix="/approvals", tags=["approvals"])

@router.post("/{subscription_id}", response_model=SubscriptionOut)
def decide(subscription_id: int, payload: ApprovalIn, db: Session = Depends(get_db), me = Depends(get_current_user)):
    sub = db.query(Subscription).filter_by(id=subscription_id).first()
    if not sub:
        raise HTTPException(404, "Not found")
    dec = payload.decision.lower()
    db.add(Approval(user_id=sub.user_id, subscription_id=sub.id, decision=dec))
    if dec == "deny":
        sub.status = SubStatus.canceling
    # log
    user = db.query(User).filter_by(email=me.email).first()
    log_event(db, user.id, "approval.decide", f"{dec.upper()} {sub.merchant}", {"subscription_id": sub.id})
    db.commit(); db.refresh(sub)
    return sub
