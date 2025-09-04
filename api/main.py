# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text
import os

# Load local .env in dev; on Render you'll use env vars
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from .db import Base, engine
from .routers import (
    auth,
    institutions,
    subscriptions,
    approvals,
    cancellations,
    plaid,
    events,
)

app = FastAPI(title="Approval v2 API")

# Create tables
Base.metadata.create_all(bind=engine)

# ---------- one-time schema upgrades (idempotent) ----------
def _upgrade_schema():
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            conn.exec_driver_sql(
                "ALTER TABLE subscriptions "
                "ADD COLUMN IF NOT EXISTS cancel_status TEXT DEFAULT 'active';"
            )
            conn.exec_driver_sql(
                "ALTER TABLE subscriptions "
                "ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMPTZ;"
            )
        elif engine.dialect.name == "sqlite":
            # add cancel_status
            try:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN cancel_status TEXT DEFAULT 'active'"
                )
            except Exception:
                pass
            # add canceled_at
            try:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN canceled_at DATETIME"
                )
            except Exception:
                pass
            # legacy: add snoozed_until column if you used it locally
            try:
                conn.exec_driver_sql(
                    "ALTER TABLE subscriptions ADD COLUMN snoozed_until DATETIME"
                )
            except Exception:
                pass

_upgrade_schema()
# -----------------------------------------------------------

# CORS (relax for now; tighten later to your Vercel origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(subscriptions.router)
app.include_router(approvals.router)
app.include_router(cancellations.router)
app.include_router(plaid.router)
app.include_router(events.router)

@app.get("/")
def root():
    return {"ok": True}

@app.get("/healthz")
def healthz():
    return {"ok": True}
