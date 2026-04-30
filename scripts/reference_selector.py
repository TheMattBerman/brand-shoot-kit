#!/usr/bin/env python3
"""Deterministic reference-image selection helpers."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import ipaddress
import json
import re


POSITIVE_PRODUCT_TOKENS = {
    "product",
    "pack",
    "package",
    "packaging",
    "packshot",
    "pdp",
    "hero",
    "primary",
    "main",
    "front",
    "bottle",
    "jar",
    "bag",
    "box",
    "tub",
    "can",
    "pouch",
    "carton",
    "container",
    "mockup",
    "lifestyle",
    "clean",
    "essentials",
    "coffee-bag",
    "front-pack",
    "label-art",
}

STRONG_NEGATIVE_TOKENS = {
    "logo",
    "logos",
    "icon",
    "icons",
    "favicon",
    "sprite",
    "badge",
    "seal",
    "review",
    "reviews",
    "rating",
    "ratings",
    "testimonial",
    "testimonials",
    "nutrition",
    "facts",
    "supplement-facts",
    "nutrition-label",
    "label-panel",
    "case",
    "phone",
    "set",
    "bundle",
    "spotwear",
    "eyeprep",
    "widget",
    "widgets",
    "beamimpact",
    "nonprofit",
    "chainnonprofit",
    "causedisplayicon",
    "cause",
}

MILD_NEGATIVE_TOKENS = {
    "banner",
    "ad",
    "promo",
    "thumbnail",
    "thumb",
    "social-share",
    "ugc",
    "footer",
    "header",
    "beans-only",
    "coffee-beans",
    "mug",
    "cup",
    "latte",
    "espresso-shot",
    "story",
    "tout",
    "middle",
}


def _url_no_query(url: str) -> str:
    parsed = urlparse(url)
    # Ignore scheme so Shopify JSON-LD http URLs can match https image candidates.
    return f"{parsed.netloc}{parsed.path}".lower()


def _structured_product_image_urls(scout: Dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    json_ld = scout.get("json_ld")
    if isinstance(json_ld, list):
        for obj in json_ld:
            if not isinstance(obj, dict):
                continue
            image = obj.get("image")
            values = image if isinstance(image, list) else [image]
            for raw in values:
                if isinstance(raw, str) and raw.strip():
                    urls.add(_url_no_query(html.unescape(raw.strip())))
    product = scout.get("shopify_product_json")
    if isinstance(product, dict):
        for key in ["image", "featured_image"]:
            raw = product.get(key)
            if isinstance(raw, str) and raw.strip():
                urls.add(_url_no_query(html.unescape(raw.strip())))
        images = product.get("images")
        if isinstance(images, list):
            for raw in images:
                if isinstance(raw, str) and raw.strip():
                    urls.add(_url_no_query(html.unescape(raw.strip())))
    return urls


def is_safe_reference_url(url: str) -> bool:
    if "..." in url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    except ValueError:
        pass
    return True


def _tokenize(value: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", value.lower()) if t}


def _context_tokens(scout: Dict[str, Any]) -> set[str]:
    fields = [
        str(scout.get("product_name") or ""),
        str(scout.get("brand_name") or ""),
        str(scout.get("title") or ""),
        str(scout.get("og_title") or ""),
    ]
    toks: set[str] = set()
    for field in fields:
        field_tokens = [token for token in _tokenize(field) if len(token) >= 3]
        toks.update(field_tokens)
        if len(field_tokens) >= 2:
            acronym = "".join(token[0] for token in field_tokens)
            if len(acronym) >= 3:
                toks.add(acronym)
    return toks


def reference_url_score(url: str, confidence: float, rank: int, scout: Dict[str, Any]) -> float:
    lower = url.lower()
    tokens = _tokenize(lower)
    score = confidence * 100.0

    path_lower = urlparse(lower).path
    if path_lower.endswith(".svg"):
        score -= 500.0

    strong_negative_hits = len(tokens & STRONG_NEGATIVE_TOKENS)
    mild_negative_hits = len(tokens & MILD_NEGATIVE_TOKENS)
    positive_hits = len(tokens & POSITIVE_PRODUCT_TOKENS)

    score += positive_hits * 40.0
    score -= strong_negative_hits * 160.0
    score -= mild_negative_hits * 25.0

    if "label" in tokens:
        score += 8.0
    if "nutrition" in tokens or "facts" in tokens:
        score -= 220.0

    context = _context_tokens(scout)
    context_hits = len(tokens & context)
    score += min(5, context_hits) * 28.0

    structured_product_images = _structured_product_image_urls(scout)
    if _url_no_query(url) in structured_product_images:
        score += 160.0

    product_name = str(scout.get("product_name") or scout.get("title") or "")
    product_tokens = [t for t in _tokenize(product_name) if len(t) >= 3]
    product_phrase_hits = sum(1 for token in product_tokens if token in lower)
    score += min(4, product_phrase_hits) * 22.0

    # Common ecommerce shorthand: peptide lip treatment -> PLT. This prevents
    # cross-sell assets with generic "main" filenames from beating the actual SKU.
    if {"peptide", "lip", "treatment"}.issubset(set(product_tokens)):
        if "plt" in tokens or "lip" in tokens:
            score += 90.0
        else:
            score -= 45.0

    # Coffee-specific guard: prefer bag/pack label references over mug/beans context shots.
    category_hint = " ".join(
        [
            str(scout.get("product_category") or ""),
            str(scout.get("product_type") or ""),
            str(scout.get("product_name") or ""),
            str(scout.get("title") or ""),
        ]
    ).lower()
    if any(k in category_hint for k in {"coffee", "roast", "bean", "espresso", "brew"}):
        bag_hits = len(tokens & {"bag", "pack", "package", "packshot", "front", "label"})
        mug_hits = len(tokens & {"mug", "cup", "latte", "beans", "espresso"})
        score += bag_hits * 45.0
        score -= mug_hits * 52.0

    # Prefer early-ranked sources slightly while keeping token semantics dominant.
    score -= rank * 0.05
    return score


def pick_auto_reference_url_from_scout(scout: Dict[str, Any]) -> Optional[str]:
    candidates: List[Tuple[float, int, str]] = []

    evidence = scout.get("image_evidence")
    if isinstance(evidence, list):
        for idx, item in enumerate(evidence):
            if not isinstance(item, dict):
                continue
            url = html.unescape(str(item.get("url") or "").strip())
            if not url:
                continue
            try:
                confidence = float(item.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            try:
                rank = int(item.get("rank"))
            except (TypeError, ValueError):
                rank = idx + 1
            score = reference_url_score(url, confidence, rank, scout)
            candidates.append((score, rank, url))

    urls = scout.get("image_urls")
    if isinstance(urls, list):
        for idx, raw in enumerate(urls):
            url = html.unescape(str(raw).strip())
            if not url:
                continue
            rank = idx + 1001
            score = reference_url_score(url, 0.0, rank, scout)
            candidates.append((score, rank, url))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    for _score, _rank, url in candidates:
        if is_safe_reference_url(url):
            return url
    return None


def pick_auto_reference_url(packet_dir: Path) -> Optional[str]:
    scout_path = packet_dir / "scout.json"
    if not scout_path.exists():
        return None
    try:
        scout = json.loads(scout_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return pick_auto_reference_url_from_scout(scout)
