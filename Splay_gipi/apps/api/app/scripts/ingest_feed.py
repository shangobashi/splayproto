from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List

import requests

from app import db
from app.providers.embedding import EmbeddingProvider


def _load_records(path: Path) -> List[Dict[str, str]]:
    if path.suffix.lower() in {".json"}:
        return json.loads(path.read_text(encoding="utf-8"))
    records: List[Dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def _fetch_to_tmp(url: str) -> Path:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    tmp = Path(".data") / "feed_download"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(resp.content)
    return tmp


def _normalize_category(value: str) -> str:
    v = (value or "").strip().lower().replace(" ", "_")
    mapping = {
        "couch": "sofa",
        "sofas": "sofa",
        "coffee_table": "coffee_table",
        "side_table": "side_table",
        "dining_table": "dining_table",
        "chair": "chair",
        "floor_lamp": "floor_lamp",
        "table_lamp": "table_lamp",
        "pendant_light": "pendant_light",
        "lamp": "table_lamp",
    }
    return mapping.get(v, "chair")


def _iter_products(records: Iterable[Dict[str, str]]) -> Iterable[Dict[str, object]]:
    for row in records:
        name = str(row.get("name") or row.get("title") or "").strip()
        brand = str(row.get("brand") or row.get("vendor") or "Retailer").strip()
        category = _normalize_category(row.get("category") or row.get("type") or "")
        price_raw = row.get("price") or row.get("price_amount") or "0"
        try:
            price = float(str(price_raw).replace("$", "").replace(",", ""))
        except ValueError:
            price = 0.0
        yield {
            "external_id": row.get("external_id") or row.get("id") or row.get("sku") or row.get("product_id"),
            "source": row.get("source") or "feed",
            "name": name,
            "brand": brand,
            "category": category,
            "price": price,
            "product_url": row.get("product_url") or row.get("url") or row.get("link"),
            "image_url": row.get("image_url") or row.get("image") or row.get("thumbnail"),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to CSV/JSON product feed")
    parser.add_argument("--url", help="URL to CSV/JSON product feed")
    args = parser.parse_args()

    if not args.path and not args.url:
        raise SystemExit("Provide --path or --url for a product feed.")

    db.init_db()
    if args.url:
        path = _fetch_to_tmp(args.url)
    else:
        path = Path(args.path)

    records = _load_records(path)
    emb = EmbeddingProvider()

    for prod in _iter_products(records):
        text = f"{prod.get('name','')} {prod.get('brand','')} {prod.get('category','')}"
        vec = emb.embed_text(text)
        prod["embedding_json"] = json.dumps(vec)
        db.upsert_product(prod)

    print(f"Ingested {len(records)} products.")


if __name__ == "__main__":
    main()
