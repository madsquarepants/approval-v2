from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth as auth_router
from .routers import merchant_charge_intents as mci_router
from .routers import user_charge_intents as uci_router
from .routers import merchant_webhook as mw_router
from .db import Base, engine

app = FastAPI(title="Approval MVP")
Base.metadata.create_all(bind=engine)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://approval-v2.vercel.app"],  # Explicitly allow frontend origin
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["GET", "POST", "OPTIONS"],  # Required methods
    allow_headers=["Authorization", "Content-Type"],  # Required headers
)

app.include_router(auth_router.router)
app.include_router(mci_router.router)
app.include_router(uci_router.router)
app.include_router(mw_router.router)

@app.get("/")
def root():
    return {"ok": True}
