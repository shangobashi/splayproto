from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


@dataclass(frozen=True)
class CatalogProduct:
    external_id: str
    name: str
    brand: str
    category: str
    price: float
    product_url: str
    image_url: Optional[str]
    source: str


class CatalogProvider:
    def __init__(self) -> None:
        self.provider = os.getenv("PRODUCT_SEARCH_PROVIDER", "serpapi").lower()

    def search(self, *, query: str, category: str, limit: int = 5) -> List[CatalogProduct]:
        if self.provider == "serper":
            return _serper_search(query, category, limit)
        if self.provider == "serpapi":
            return _serpapi_search(query, category, limit)
        return _fallback_search(query, category, limit)


def _serpapi_search(query: str, category: str, limit: int) -> List[CatalogProduct]:
    key = os.getenv("SERPAPI_API_KEY")
    if not key:
        return _fallback_search(query, category, limit)
    if requests is None:
        return _fallback_search(query, category, limit)
    params = {
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "us",
        "api_key": key,
    }
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("shopping_results") or []
    except Exception:
        return _fallback_search(query, category, limit)
    out: List[CatalogProduct] = []
    for it in items[:limit]:
        price = _parse_price(it.get("price"))
        out.append(
            CatalogProduct(
                external_id=str(it.get("product_id") or it.get("link")),
                name=str(it.get("title") or "").strip(),
                brand=str(it.get("source") or "Retailer"),
                category=category,
                price=price,
                product_url=str(it.get("link") or ""),
                image_url=it.get("thumbnail"),
                source="serpapi",
            )
        )
    return [p for p in out if p.product_url]


def _serper_search(query: str, category: str, limit: int) -> List[CatalogProduct]:
    key = os.getenv("SERPER_API_KEY")
    if not key:
        return _fallback_search(query, category, limit)
    if requests is None:
        return _fallback_search(query, category, limit)
    headers = {"X-API-KEY": key, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "us", "hl": "en"}
    try:
        resp = requests.post("https://google.serper.dev/shopping", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("shopping") or []
    except Exception:
        return _fallback_search(query, category, limit)
    out: List[CatalogProduct] = []
    for it in items[:limit]:
        price = _parse_price(it.get("price"))
        out.append(
            CatalogProduct(
                external_id=str(it.get("productId") or it.get("link")),
                name=str(it.get("title") or "").strip(),
                brand=str(it.get("source") or "Retailer"),
                category=category,
                price=price,
                product_url=str(it.get("link") or ""),
                image_url=it.get("imageUrl"),
                source="serper",
            )
        )
    return [p for p in out if p.product_url]


def _fallback_search(query: str, category: str, limit: int) -> List[CatalogProduct]:
    # Last resort: return retailer search links (not product pages).
    retailers = [
        ("Wayfair", "https://www.wayfair.com/keyword.php?keyword="),
        ("IKEA", "https://www.ikea.com/us/en/search/?q="),
        ("West Elm", "https://www.westelm.com/search/results.html?words="),
    ]
    out: List[CatalogProduct] = []
    for i in range(min(limit, len(retailers))):
        brand, base = retailers[i]
        url = base + query.replace(" ", "+")
        out.append(
            CatalogProduct(
                external_id=url,
                name=f"{query} (search results)",
                brand=brand,
                category=category,
                price=0.0,
                product_url=url,
                image_url=None,
                source="fallback",
            )
        )
    return out


def _parse_price(raw: object) -> float:
    if raw is None:
        return 0.0
    s = str(raw)
    digits = "".join(ch for ch in s if (ch.isdigit() or ch == "."))
    try:
        return float(digits) if digits else 0.0
    except ValueError:
        return 0.0
