from fastapi.testclient import TestClient
import os
from app.main import app
from app.db import init_db
from app.scripts.seed_products import main as seed_products

client = TestClient(app)

def setup_module(_m):
    os.environ["DB_PATH"] = ".data/test.db"
    os.environ["UPLOAD_DIR"] = ".data/test_uploads"
    init_db()
    seed_products()

def test_dev_login():
    r = client.post("/auth/dev-login", json={"email":"a@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body

def test_create_scan_and_poll_pending():
    # deterministic fake "image"
    img = b"\xff\xd8\xff" + b"0"*1024
    r = client.post("/scans", files={"image": ("room.jpg", img, "image/jpeg")})
    assert r.status_code == 200
    scan_id = r.json()["scan_id"]
    g = client.get(f"/scans/{scan_id}")
    assert g.status_code == 200
    assert g.json()["status"] in ("pending","processing","done")
