from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, List, Tuple

Vector = List[float]

@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    category: str
    price: float
    affiliate_url: str
    embedding: Vector

def cosine_similarity(a: Vector, b: Vector) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = sqrt(sum(x*x for x in a))
    nb = sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def rank_products(query: Vector, products: Iterable[Product], *, top_k: int = 5) -> List[Tuple[Product, float]]:
    scored = [(p, cosine_similarity(query, p.embedding)) for p in products]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]

def pick_budget_alternatives(ranked: List[Tuple[Product, float]], *, top: Product, k: int = 2) -> List[Product]:
    # Budget = cheaper than top product, then highest similarity.
    cheaper = [p for p, _s in ranked if p.price < top.price]
    return cheaper[:k]
