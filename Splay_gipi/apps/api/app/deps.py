from __future__ import annotations
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.security import verify_token

bearer = HTTPBearer(auto_error=False)

def get_optional_user_id(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str | None:
    if creds is None:
        return None
    return verify_token(creds.credentials)
