from __future__ import annotations
import base64
import json
import os
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, List

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None
try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None

SUPPORTED = [
    "sofa",
    "coffee_table",
    "side_table",
    "dining_table",
    "chair",
    "floor_lamp",
    "table_lamp",
    "pendant_light",
]


@dataclass(frozen=True)
class Detected:
    category: str
    bbox: Dict[str, float]  # normalized 0..1
    confidence: float
    query: str  # free-text description for product search


class VisionProvider:
    def __init__(self) -> None:
        self.provider = os.getenv("VISION_PROVIDER", "auto").lower()
        self.model = os.getenv("VISION_MODEL", "gemini-2.0-flash")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if OpenAI else None

    def detect(self, image_bytes: bytes) -> List[Detected]:
        if self.provider == "auto":
            for fn in (self._detect_gemini, self._detect_anthropic, self._detect_openai):
                items = fn(image_bytes)
                if items:
                    return items
            return _HashVisionProvider().detect(image_bytes)
        if self.provider == "gemini":
            return self._detect_gemini(image_bytes) or _HashVisionProvider().detect(image_bytes)
        if self.provider == "anthropic":
            return self._detect_anthropic(image_bytes) or _HashVisionProvider().detect(image_bytes)
        if self.provider == "openai":
            return self._detect_openai(image_bytes) or _HashVisionProvider().detect(image_bytes)
        if self.provider == "hash":
            return _HashVisionProvider().detect(image_bytes)
        return _HashVisionProvider().detect(image_bytes)

    def _detect_openai(self, image_bytes: bytes) -> List[Detected]:
        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            return []
        b64 = base64.b64encode(image_bytes).decode("ascii")
        system = "You are a vision system for furniture detection. Return only JSON."
        user = {
            "role": "user",
            "content": [
                {"type": "text", "text": _prompt_text()},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }
        try:
            resp = self.client.chat.completions.create(
                model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
                messages=[{"role": "system", "content": system}, user],
                temperature=0.2,
            )
            text = resp.choices[0].message.content or "[]"
            return _parse_detected(_parse_json(text))
        except Exception as exc:
            print(f"vision openai failed: {exc}")
            return []

    def _detect_gemini(self, image_bytes: bytes) -> List[Detected]:
        key = os.getenv("GEMINI_API_KEY")
        if not key or requests is None:
            return []
        b64 = base64.b64encode(image_bytes).decode("ascii")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": _prompt_text()},
                        {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=45)
                if resp.status_code == 429 and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = _extract_text_from_gemini(data)
                return _parse_detected(_parse_json(text))
            except Exception as exc:
                if attempt >= 2:
                    print(f"vision gemini failed: {exc}")
                    return []
        return []

    def _detect_anthropic(self, image_bytes: bytes) -> List[Detected]:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key or requests is None:
            return []
        b64 = base64.b64encode(image_bytes).decode("ascii")
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": os.getenv("ANTHROPIC_VISION_MODEL", "claude-3-5-sonnet-20240620"),
            "max_tokens": 800,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _prompt_text()},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                    ],
                }
            ],
        }
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            text = _extract_text_from_anthropic(data)
            return _parse_detected(_parse_json(text))
        except Exception as exc:
            print(f"vision anthropic failed: {exc}")
            return []


class _HashVisionProvider:
    def detect(self, image_bytes: bytes) -> List[Detected]:
        h = sha256(image_bytes).hexdigest()
        idxs = [int(h[i:i + 2], 16) % len(SUPPORTED) for i in (0, 2, 4)]
        color = _dominant_color_name(image_bytes)
        items: List[Detected] = []
        for j, i in enumerate(idxs):
            cat = SUPPORTED[i]
            x = 0.08 + (j * 0.28)
            y = 0.18 + (j * 0.06)
            w = 0.32
            hh = 0.28
            conf = 0.55 + (int(h[6 + 2 * j:8 + 2 * j], 16) % 30) / 100.0
            query = f"{color} {cat.replace('_', ' ')}".strip()
            items.append(
                Detected(
                    category=cat,
                    bbox={"x": x, "y": y, "w": w, "h": hh},
                    confidence=min(conf, 0.95),
                    query=query,
                )
            )
        return items


def _prompt_text() -> str:
    return (
        "Detect the main furniture items in the room photo. "
        "Use only these categories: "
        + ", ".join(SUPPORTED)
        + ". "
        "Return JSON array with objects: "
        "{category, bbox:{x,y,w,h}, confidence, query}. "
        "bbox values must be normalized 0..1. "
        "query should be a short descriptive phrase including "
        "style/material/color (e.g., 'mid-century walnut coffee table')."
    )


def _dominant_color_name(image_bytes: bytes) -> str:
    if Image is None:
        return "neutral"
    try:
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((48, 48))
        pixels = list(img.getdata())
        r = sum(p[0] for p in pixels) / len(pixels)
        g = sum(p[1] for p in pixels) / len(pixels)
        b = sum(p[2] for p in pixels) / len(pixels)
        return _rgb_to_name(r, g, b)
    except Exception:
        return "neutral"


def _rgb_to_name(r: float, g: float, b: float) -> str:
    if r < 50 and g < 50 and b < 50:
        return "black"
    if r > 210 and g > 210 and b > 210:
        return "white"
    if r > 180 and g > 140 and b < 90:
        return "tan"
    if r > 180 and g > 140 and b > 120:
        return "beige"
    if r > 160 and g < 120 and b < 120:
        return "red"
    if g > 160 and r < 120:
        return "green"
    if b > 160 and r < 120:
        return "blue"
    return "neutral"


def _parse_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _extract_json_array(text)


def _extract_json_array(text: str) -> List[Dict[str, object]]:
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
    return []


def _extract_text_from_gemini(payload: Dict[str, object]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return "[]"
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    texts = []
    for part in parts:
        txt = part.get("text")
        if isinstance(txt, str):
            texts.append(txt)
    return "\n".join(texts) if texts else "[]"


def _extract_text_from_anthropic(payload: Dict[str, object]) -> str:
    content = payload.get("content") or []
    texts = []
    for part in content:
        if part.get("type") == "text":
            txt = part.get("text")
            if isinstance(txt, str):
                texts.append(txt)
    return "\n".join(texts) if texts else "[]"


def _parse_detected(data) -> List[Detected]:
    items: List[Detected] = []
    for item in data or []:
        cat = str(item.get("category", "")).strip()
        if cat not in SUPPORTED:
            continue
        bbox = item.get("bbox") or {}
        query = str(item.get("query", cat.replace("_", " "))).strip()
        items.append(
            Detected(
                category=cat,
                bbox={
                    "x": _clamp01(float(bbox.get("x", 0.1))),
                    "y": _clamp01(float(bbox.get("y", 0.1))),
                    "w": _clamp01(float(bbox.get("w", 0.4))),
                    "h": _clamp01(float(bbox.get("h", 0.3))),
                },
                confidence=float(item.get("confidence", 0.8)),
                query=query,
            )
        )
    return items


def _clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v
