from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from app import db
from app.security import sign_token

router = APIRouter()

class DevLoginRequest(BaseModel):
    email: EmailStr

@router.post("/dev-login")
def dev_login(req: DevLoginRequest):
    user = db.upsert_user(req.email)
    token = sign_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "is_premium": bool(user["is_premium"])}}
