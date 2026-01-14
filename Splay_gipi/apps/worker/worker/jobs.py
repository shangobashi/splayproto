from __future__ import annotations
import json, os
from pathlib import Path
from typing import List
from PIL import Image

# Import api-side modules by path (simple MVP hack).
import sys
API_APP = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_APP))

from app import db
from app.providers.vision import VisionProvider
from app.providers.embedding import EmbeddingProvider
from app.providers.catalog import CatalogProvider
from matching_core.ranking import Product, rank_products, pick_budget_alternatives

def _load_products(category: str) -> List[Product]:
    rows = db.list_products_by_category(category)
    out: List[Product] = []
    for r in rows:
        out.append(Product(
            id=r["id"],
            name=r["name"],
            brand=r["brand"],
            category=r["category"],
            price=float(r["price"]),
            affiliate_url=r["affiliate_url"],
            embedding=json.loads(r["embedding_json"]),
        ))
    return out

def process_scan(scan_id: str) -> None:
    scan = db.get_scan(scan_id)
    if not scan:
        return
    db.update_scan_status(scan_id, "processing")
    image_path = scan["image_path"]
    blob = Path(image_path).read_bytes()

    vision = VisionProvider()
    emb = EmbeddingProvider()
    catalog = CatalogProvider()
    catalog_mode = os.getenv("CATALOG_MODE", "search").lower()

    detected = vision.detect(blob)

    for det in detected:
        item_id = db.insert_detected_item(scan_id, det.category, det.bbox, det.confidence)
        query_text = getattr(det, "query", det.category.replace("_", " "))
        if catalog_mode == "local":
            qvec = emb.embed_text(query_text)
            products = _load_products(det.category)
            ranked = rank_products(qvec, products, top_k=10)
            if not ranked:
                continue
            top = ranked[0][0]
            budgets = pick_budget_alternatives(ranked, top=top, k=2)
            db.insert_match(item_id, top.id, rank=1, is_budget=False)
            r = 2
            for b in budgets:
                db.insert_match(item_id, b.id, rank=r, is_budget=True)
                r += 1
        else:
            results = catalog.search(query=query_text, category=det.category, limit=5)
            if not results:
                continue
            ranked_results = _rank_search_results(results)
            r = 1
            for prod in ranked_results:
                pid = db.upsert_product({
                    "external_id": prod.external_id,
                    "source": prod.source,
                    "name": prod.name,
                    "brand": prod.brand,
                    "category": prod.category,
                    "price": prod.price,
                    "affiliate_url": prod.product_url,
                    "product_url": prod.product_url,
                    "image_url": prod.image_url,
                })
                db.insert_match(item_id, pid, rank=r, is_budget=(r > 1))
                r += 1

    db.update_scan_status(scan_id, "done")


def _rank_search_results(products):
    # Basic rank: keep order, but mark cheaper options as budget after the first.
    if not products:
        return []
    return products
