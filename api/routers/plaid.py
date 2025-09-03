from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os, requests

from ..db import get_db
from ..deps import get_current_user
from ..models import InstitutionConnection, User

router = APIRouter(prefix="/plaid", tags=["plaid"])

PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
BASES = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}
BASE = BASES[PLAID_ENV]
CID = os.getenv("PLAID_CLIENT_ID")
SEC = os.getenv("PLAID_SECRET")
PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")

def plaid_req(path: str, payload: dict):
    if not (CID and SEC):
        raise HTTPException(500, "Plaid keys not set in .env")
    body = {"client_id": CID, "secret": SEC, **payload}
    r = requests.post(f"{BASE}{path}", json=body, timeout=20)
    if not r.ok:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@router.post("/link_token")
def create_link_token(db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    data = plaid_req("/link/token/create", {
        "user": {"client_user_id": str(user.id)},
        "client_name": "Approval v2",
        "products": PRODUCTS,
        "country_codes": COUNTRY_CODES,
        "language": "en",
    })
    return {"link_token": data["link_token"]}

class PublicTokenIn(BaseModel):
    public_token: str

@router.post("/exchange")
def exchange_public_token(payload: PublicTokenIn, db: Session = Depends(get_db), me = Depends(get_current_user)):
    data = plaid_req("/item/public_token/exchange", {
        "public_token": payload.public_token
    })
    access_token = data["access_token"]
    user = db.query(User).filter_by(email=me.email).first()
    conn = InstitutionConnection(
        user_id=user.id, provider="plaid", status="linked", access_token_ref=access_token
    )
    db.add(conn); db.commit()
    return {"status": "linked"}

