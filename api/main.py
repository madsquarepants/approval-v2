# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

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

# --- SQLite-only schema tweak (skip on Postgres/Render) ---
from sqlalchemy import text  # noqa: E402
if engine.dialect.name == "sqlite":
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql(
                'ALTER TABLE subscriptions ADD COLUMN snoozed_until DATETIME'
            )
        except Exception:
            # column already exists or table not present yet
            pass
# ----------------------------------------------------------

# CORS (relax for now; tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
