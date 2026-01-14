from __future__ import annotations
import os, pathlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.deps import get_optional_user_id
from app import db
from app.queue import enqueue_scan

router = APIRouter()

def _ensure_upload_dir() -> str:
    d = os.getenv("UPLOAD_DIR", ".data/uploads")
    os.makedirs(d, exist_ok=True)
    return d

@router.post("/scans")
async def create_scan(image: UploadFile = File(...), user_id: str | None = Depends(get_optional_user_id)):
    if image.content_type not in ("image/jpeg","image/png","image/webp","image/heic","image/heif"):
        raise HTTPException(status_code=415, detail="Unsupported image type")
    # free tier limit (counts scans)
    if user_id:
        user = db.upsert_user(email="placeholder@local")  # not used; we just ensure table exists
    if user_id:
        # naive: limit counts all scans; good enough for MVP
        limit = int(os.getenv("FREE_SCAN_LIMIT","3"))
        scans = db.count_scans_for_user(user_id)
        if scans >= limit:
            raise HTTPException(status_code=429, detail="Free scan limit exceeded")
    updir = _ensure_upload_dir()
    content = await image.read()
    filename = f"{pathlib.Path(image.filename or 'upload').stem}_{os.urandom(4).hex()}.bin"
    path = os.path.join(updir, filename)
    with open(path, "wb") as f:
        f.write(content)
    scan_id = db.create_scan(user_id, path)
    try:
        enqueue_scan(scan_id)
    except Exception as exc:
        db.update_scan_status(scan_id, "failed")
        print(f"scan {scan_id} failed: {exc}")
    return {"scan_id": scan_id}

@router.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    scan = db.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Not found")
    items = db.list_items_with_matches(scan_id) if scan["status"] == "done" else []
    return {"id": scan["id"], "status": scan["status"], "created_at": scan["created_at"], "items": items}
