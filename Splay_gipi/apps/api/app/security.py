from __future__ import annotations
import os, time
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

def sign_token(user_id: str) -> str:
    secret = os.getenv("JWT_SECRET", "dev-secret")
    payload = {"sub": user_id, "iat": int(time.time())}
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token: str) -> str:
    secret = os.getenv("JWT_SECRET", "dev-secret")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return str(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
