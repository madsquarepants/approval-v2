from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import InstitutionConnection, User
from ..deps import get_current_user

router = APIRouter(prefix="/institutions", tags=["institutions"])

@router.post("/link")
def link_account(provider: str = "plaid", db: Session = Depends(get_db), me = Depends(get_current_user)):
    # Stub: create a fake link to simulate success
    user = db.query(User).filter_by(email=me.email).first()
    conn = InstitutionConnection(user_id=user.id,
                                 provider=provider,
                                 status="linked",
                                 access_token_ref="fake_ref")
    db.add(conn); db.commit()
    return {"status": "linked"}
