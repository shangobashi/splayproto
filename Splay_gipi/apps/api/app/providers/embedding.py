from __future__ import annotations
import hashlib
import os
from typing import List

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


class EmbeddingProvider:
    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim
        self.provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if OpenAI else None

    def embed_text(self, text: str) -> List[float]:
        if self.provider != "openai" or not os.getenv("OPENAI_API_KEY") or not OpenAI:
            return _stub_embed(text.encode("utf-8"), self.dim)
        try:
            resp = self.client.embeddings.create(
                model=self.model,
                input=[text],
            )
            return list(resp.data[0].embedding)
        except Exception:
            return _stub_embed(text.encode("utf-8"), self.dim)

    def embed(self, blob: bytes) -> List[float]:
        # Backwards-compatible helper for legacy code paths.
        if self.provider != "openai" or not os.getenv("OPENAI_API_KEY") or not OpenAI:
            return _stub_embed(blob, self.dim)
        text = blob.decode("utf-8", errors="ignore")
        if not text.strip():
            text = "image"
        return self.embed_text(text)


def _stub_embed(blob: bytes, dim: int) -> List[float]:
    h = hashlib.sha256(blob).digest()
    out: List[float] = []
    for i in range(dim):
        b = h[i % len(h)]
        out.append((b / 127.5) - 1.0)
    return out
