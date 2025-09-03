from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from ..db import get_db
from ..models import Subscription, User, SubStatus
from ..schemas import SubscriptionOut
from ..deps import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

FAKE_SET = [
    {"merchant": "Netflix", "plan": "Standard", "amount": 15.49, "interval": "monthly"},
    {"merchant": "Spotify", "plan": "Premium", "amount": 10.99, "interval": "monthly"},
    {"merchant": "LA Fitness", "plan": "Single Club", "amount": 34.99, "interval": "monthly"}
]

@router.post("/scan", response_model=list[SubscriptionOut])
def scan(db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    out = []
    for it in FAKE_SET:
        s = Subscription(user_id=user.id,
                         merchant=it["merchant"],
                         plan=it.get("plan"),
                         amount=it["amount"],
                         interval=it["interval"],
                         next_renewal_at=datetime.utcnow(),
                         status=SubStatus.active)
        db.add(s); db.flush()
        out.append(s)
    db.commit()
    return out

@router.get("/", response_model=list[SubscriptionOut])
def list_subs(db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    subs = db.query(Subscription).filter_by(user_id=user.id).all()
    return subs

# --- REAL SCAN (Plaid) ---
import os, requests, math
from datetime import timedelta, date
from collections import defaultdict
from ..models import InstitutionConnection

PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
BASES = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}
BASE = BASES[PLAID_ENV]
CID = os.getenv("PLAID_CLIENT_ID")
SEC = os.getenv("PLAID_SECRET")

def plaid_req(path: str, payload: dict):
    if not (CID and SEC):
        raise HTTPException(500, "Plaid keys not set")
    body = {"client_id": CID, "secret": SEC, **payload}
    r = requests.post(f"{BASE}{path}", json=body, timeout=20)
    if not r.ok:
        raise HTTPException(r.status_code, r.text)
    return r.json()

def normalize_name(s: str) -> str:
    s = (s or "").lower()
    junk = [" inc", " llc", ".com", " subscription", " member", "*", "-", "_"]
    for j in junk: s = s.replace(j, " ")
    s = " ".join(s.split())
    # Simple canonical map
    if "netflix" in s: return "Netflix"
    if "spotify" in s: return "Spotify"
    if "la fitness" in s or "lafitness" in s: return "LA Fitness"
    if "apple" in s and "services" in s: return "Apple Services"
    if "microsoft" in s: return "Microsoft"
    if "google" in s or "youtube" in s: return "Google/YouTube"
    return s.title()

def looks_monthly(dates):
    if len(dates) < 2: return False
    dates = sorted(dates)
    gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    # any gap roughly monthly?
    return any(20 <= g <= 40 for g in gaps)

@router.post("/scan_real", response_model=list[SubscriptionOut])
def scan_real(db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    conn = (
        db.query(InstitutionConnection)
        .filter_by(user_id=user.id, provider="plaid")
        .order_by(InstitutionConnection.id.desc())
        .first()
    )
    if not conn:
        raise HTTPException(400, "No Plaid connection for user")

    today = date.today()
    start = (today - timedelta(days=90)).isoformat()
    end = today.isoformat()

    data = plaid_req("/transactions/get", {
        "access_token": conn.access_token_ref,
        "start_date": start,
        "end_date": end,
        "options": {"count": 500, "offset": 0}
    })
    txns = data.get("transactions", [])

    # group by normalized merchant + rounded amount
    groups = defaultdict(lambda: {"dates": [], "amounts": []})
    for t in txns:
        nm = normalize_name(t.get("merchant_name") or t.get("name") or "")
        amt = abs(float(t.get("amount", 0)))
        dt = datetime.fromisoformat(t.get("date"))
        key = (nm, round(amt, 2))
        groups[key]["dates"].append(dt)
        groups[key]["amounts"].append(amt)

    created_or_updated = []
    for (merchant, amt_key), info in groups.items():
        if len(info["dates"]) < 2: 
            continue
        if not looks_monthly(info["dates"]):
            continue
        amount = round(sum(info["amounts"]) / len(info["amounts"]), 2)
        next_renew = max(info["dates"]) + timedelta(days=30)

        existing = db.query(Subscription).filter_by(user_id=user.id, merchant=merchant).first()
        if not existing:
            s = Subscription(
                user_id=user.id,
                merchant=merchant,
                plan=None,
                amount=amount,
                interval="monthly",
                next_renewal_at=next_renew,
                status=SubStatus.active
            )
            db.add(s); db.flush()
            created_or_updated.append(s)
        else:
            existing.amount = amount
            existing.interval = "monthly"
            existing.next_renewal_at = next_renew
            existing.status = SubStatus.active
            created_or_updated.append(existing)

    db.commit()
    # return user’s current subs
    return db.query(Subscription).filter_by(user_id=user.id).all()


# --- UPCOMING RENEWALS ---
from datetime import timedelta  # top of file already imports datetime

@router.get("/upcoming", response_model=list[SubscriptionOut])
def upcoming(days: int = 7, db: Session = Depends(get_db), me = Depends(get_current_user)):
    user = db.query(User).filter_by(email=me.email).first()
    cutoff = datetime.utcnow() + timedelta(days=days)
    subs = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status.in_([SubStatus.active, SubStatus.canceling]),
            Subscription.next_renewal_at.isnot(None),
            Subscription.next_renewal_at <= cutoff,
        )
        .order_by(Subscription.next_renewal_at.asc())
        .all()
    )
    return subs

