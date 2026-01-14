from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import auth, scans
from app.db import init_db

load_dotenv()
app = FastAPI(title="Splay API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(scans.router, prefix="", tags=["scans"])


@app.on_event("startup")
def _startup() -> None:
    # Ensure DB schema is up to date for real integrations.
    init_db()

