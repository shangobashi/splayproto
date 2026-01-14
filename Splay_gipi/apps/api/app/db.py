from __future__ import annotations
import json, os, sqlite3, uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"

@dataclass
class Settings:
    db_path: str

def get_settings() -> Settings:
    db_path = os.getenv("DB_PATH", ".data/app.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return Settings(db_path=db_path)

def connect() -> sqlite3.Connection:
    s = get_settings()
    con = sqlite3.connect(s.db_path)
    con.row_factory = sqlite3.Row
    return con

def init_db() -> None:
    con = connect()
    cur = con.cursor()
    cur.executescript(
        '''
        CREATE TABLE IF NOT EXISTS users(
          id TEXT PRIMARY KEY,
          email TEXT UNIQUE NOT NULL,
          is_premium INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scans(
          id TEXT PRIMARY KEY,
          user_id TEXT NULL,
          image_path TEXT NOT NULL,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS detected_items(
          id TEXT PRIMARY KEY,
          scan_id TEXT NOT NULL,
          category TEXT NOT NULL,
          bbox_x REAL NOT NULL,
          bbox_y REAL NOT NULL,
          bbox_w REAL NOT NULL,
          bbox_h REAL NOT NULL,
          confidence REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products(
          id TEXT PRIMARY KEY,
          external_id TEXT,
          source TEXT,
          name TEXT NOT NULL,
          brand TEXT NOT NULL,
          category TEXT NOT NULL,
          price REAL NOT NULL,
          affiliate_url TEXT NOT NULL,
          product_url TEXT,
          image_url TEXT,
          availability TEXT,
          last_seen_at TEXT,
          embedding_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS matches(
          id TEXT PRIMARY KEY,
          detected_item_id TEXT NOT NULL,
          product_id TEXT NOT NULL,
          rank INTEGER NOT NULL,
          is_budget INTEGER NOT NULL
        );
        '''
    )
    con.commit()
    _ensure_columns(con, "products", {
        "external_id": "external_id TEXT",
        "source": "source TEXT",
        "product_url": "product_url TEXT",
        "image_url": "image_url TEXT",
        "availability": "availability TEXT",
        "last_seen_at": "last_seen_at TEXT",
    })
    con.close()


def _ensure_columns(con: sqlite3.Connection, table: str, cols: Dict[str, str]) -> None:
    existing = {row["name"] for row in con.execute(f"PRAGMA table_info({table})")}
    for name, ddl in cols.items():
        if name not in existing:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
    con.commit()

def upsert_user(email: str) -> Dict[str, Any]:
    con = connect()
    cur = con.cursor()
    row = cur.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if row:
        con.close()
        return dict(row)
    user_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO users(id,email,is_premium,created_at) VALUES(?,?,?,?)",
        (user_id, email, 0, _utcnow())
    )
    con.commit()
    row = cur.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    con.close()
    return dict(row)

def count_scans_for_user(user_id: str) -> int:
    con = connect()
    cur = con.cursor()
    n = cur.execute("SELECT COUNT(*) AS n FROM scans WHERE user_id=?", (user_id,)).fetchone()["n"]
    con.close()
    return int(n)

def create_scan(user_id: Optional[str], image_path: str) -> str:
    scan_id = str(uuid.uuid4())
    con = connect()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO scans(id,user_id,image_path,status,created_at) VALUES(?,?,?,?,?)",
        (scan_id, user_id, image_path, "pending", _utcnow())
    )
    con.commit()
    con.close()
    return scan_id

def update_scan_status(scan_id: str, status: str) -> None:
    con = connect()
    con.execute("UPDATE scans SET status=? WHERE id=?", (status, scan_id))
    con.commit()
    con.close()

def get_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    con = connect()
    row = con.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
    con.close()
    return dict(row) if row else None

def insert_detected_item(scan_id: str, category: str, bbox: Dict[str,float], confidence: float) -> str:
    item_id = str(uuid.uuid4())
    con = connect()
    con.execute(
        "INSERT INTO detected_items(id,scan_id,category,bbox_x,bbox_y,bbox_w,bbox_h,confidence) VALUES(?,?,?,?,?,?,?,?)",
        (item_id, scan_id, category, bbox["x"], bbox["y"], bbox["w"], bbox["h"], confidence)
    )
    con.commit()
    con.close()
    return item_id

def list_items_with_matches(scan_id: str) -> List[Dict[str, Any]]:
    con = connect()
    items = con.execute("SELECT * FROM detected_items WHERE scan_id=?", (scan_id,)).fetchall()
    out: List[Dict[str, Any]] = []
    for it in items:
        it_d = dict(it)
        mrows = con.execute(
            "SELECT m.rank,m.is_budget,p.* FROM matches m JOIN products p ON p.id=m.product_id WHERE m.detected_item_id=? ORDER BY m.rank ASC",
            (it_d["id"],)
        ).fetchall()
        matches = []
        for mr in mrows:
            mr_d = dict(mr)
            matches.append({
                "rank": mr_d["rank"],
                "is_budget": bool(mr_d["is_budget"]),
                "product": {
                    "id": mr_d["id"],
                    "name": mr_d["name"],
                    "brand": mr_d["brand"],
                    "category": mr_d["category"],
                    "price": mr_d["price"],
                    "affiliate_url": mr_d.get("product_url") or mr_d["affiliate_url"],
                    "image_url": mr_d.get("image_url"),
                }
            })
        it_d["bbox"] = {"x": it_d.pop("bbox_x"), "y": it_d.pop("bbox_y"), "w": it_d.pop("bbox_w"), "h": it_d.pop("bbox_h")}
        it_d["matches"] = matches
        out.append(it_d)
    con.close()
    return out

def list_products_by_category(category: str) -> List[Dict[str, Any]]:
    con = connect()
    rows = con.execute("SELECT * FROM products WHERE category=?", (category,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def upsert_product(product: Dict[str, Any]) -> str:
    con = connect()
    cur = con.cursor()
    external_id = product.get("external_id")
    product_url = product.get("product_url")
    row = None
    if external_id:
        row = cur.execute("SELECT * FROM products WHERE external_id=?", (external_id,)).fetchone()
    if not row and product_url:
        row = cur.execute("SELECT * FROM products WHERE product_url=?", (product_url,)).fetchone()
    if row:
        pid = row["id"]
        cur.execute(
            "UPDATE products SET name=?,brand=?,category=?,price=?,affiliate_url=?,product_url=?,image_url=?,source=?,last_seen_at=? WHERE id=?",
            (
                product.get("name"),
                product.get("brand"),
                product.get("category"),
                product.get("price", 0.0),
                product.get("affiliate_url") or product_url or "",
                product_url,
                product.get("image_url"),
                product.get("source"),
                _utcnow(),
                pid,
            ),
        )
        con.commit()
        con.close()
        return pid
    pid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO products(id,external_id,source,name,brand,category,price,affiliate_url,product_url,image_url,availability,last_seen_at,embedding_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            pid,
            external_id,
            product.get("source"),
            product.get("name"),
            product.get("brand"),
            product.get("category"),
            product.get("price", 0.0),
            product.get("affiliate_url") or product_url or "",
            product_url,
            product.get("image_url"),
            product.get("availability"),
            _utcnow(),
            product.get("embedding_json") or "[]",
        ),
    )
    con.commit()
    con.close()
    return pid

def insert_match(detected_item_id: str, product_id: str, rank: int, is_budget: bool) -> None:
    con = connect()
    con.execute(
        "INSERT INTO matches(id,detected_item_id,product_id,rank,is_budget) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), detected_item_id, product_id, rank, 1 if is_budget else 0)
    )
    con.commit()
    con.close()
