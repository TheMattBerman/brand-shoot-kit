#!/usr/bin/env python3
"""Deterministic structured extraction for Brand Shoot scout payloads."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from packet_utils import dump_json, load_json


def clean_text(value: str) -> str:
    return " ".join((value or "").replace("|", " ").split()).strip()


def host_brand(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if not host:
        return "Unknown Brand"
    return host.split(".")[0].replace("-", " ").title()


def infer_brand_product(base: Dict[str, Any]) -> Tuple[str, str]:
    title = clean_text(str(base.get("og_title") or base.get("title") or ""))
    h1 = ""
    if isinstance(base.get("h1"), list) and base["h1"]:
        h1 = clean_text(str(base["h1"][0]))

    brand = ""
    product = ""
    if title:
        for sep in ["|", "-", "::"]:
            if sep in title:
                parts = [p.strip() for p in title.split(sep) if p.strip()]
                if len(parts) >= 2:
                    product = parts[0]
                    brand = parts[-1]
                    break
        if not product:
            product = title

    if h1 and (not product or len(h1) >= len(product)):
        product = h1
    if not brand:
        brand = host_brand(str(base.get("url", "")))
    return brand or "Unknown Brand", product or "Unknown Product"


def text_corpus(base: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ["title", "meta_description", "og_title", "og_description", "note"]:
        parts.append(str(base.get(key, "")))
    h1 = base.get("h1") or []
    if isinstance(h1, list):
        parts.extend(str(x) for x in h1[:5])
    for k in ["raw_text", "page_text", "body_text", "visible_text"]:
        if base.get(k):
            parts.append(str(base.get(k)))
    return clean_text(" ".join(parts))


def detect_price(text: str) -> str:
    m = re.search(r"(\$\s?\d{1,4}(?:\.\d{2})?)", text)
    if m:
        return m.group(1).replace(" ", "")
    m = re.search(r"(\d{1,4}(?:\.\d{2})?\s?(?:usd|dollars))", text, flags=re.I)
    return clean_text(m.group(1)) if m else ""


def detect_category_and_type(text: str) -> Tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ["serum", "cleanser", "moisturizer", "dropper", "skincare"]):
        return "skincare", "skincare bottle"
    if any(k in t for k in ["coffee", "espresso", "beans", "brew", "roast"]):
        return "coffee", "sealed coffee bag"
    if any(k in t for k in ["supplement", "greens", "powder", "vitamin", "capsule", "protein"]):
        return "supplement", "supplement tub"
    if any(k in t for k in ["candle", "jar", "home fragrance", "wax"]):
        return "home-goods", "glass jar candle"
    return "generic", "packaged consumer product"


def split_candidates(raw: str) -> List[str]:
    out: List[str] = []
    for chunk in re.split(r"[,\|/;]", raw):
        c = clean_text(chunk)
        if not c:
            continue
        if len(c) < 2:
            continue
        out.append(c)
    seen = set()
    uniq = []
    for v in out:
        lower = v.lower()
        if lower in seen:
            continue
        seen.add(lower)
        uniq.append(v)
    return uniq


def detect_variants(text: str) -> List[str]:
    items: List[str] = []
    patterns = [
        r"(?:available in|choose from|options?:)\s*([^\.]+)",
        r"(?:flavors?|scents?|sizes?|colors?|roasts?)\s*:\s*([^\.]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.I):
            items.extend(split_candidates(m.group(1)))
    return items[:8]


def sentence_chunks(text: str) -> List[str]:
    chunks = [clean_text(x) for x in re.split(r"[.!?\n]+", text) if clean_text(x)]
    return chunks[:80]


def detect_claims(text: str) -> List[str]:
    keys = [
        "supports",
        "helps",
        "benefit",
        "hydrates",
        "improves",
        "boosts",
        "non-toxic",
        "clinical",
        "freshly roasted",
        "single origin",
    ]
    out: List[str] = []
    for sent in sentence_chunks(text):
        low = sent.lower()
        if any(k in low for k in keys):
            out.append(sent)
    return out[:8]


def detect_ingredients_specs(text: str) -> List[str]:
    out: List[str] = []
    for sent in sentence_chunks(text):
        low = sent.lower()
        if "ingredients" in low or "materials" in low or "spec" in low:
            out.append(sent)
            continue
        if any(k in low for k in ["hyaluronic", "niacinamide", "caffeine", "vitamin", "protein", "net wt", "oz"]):
            out.append(sent)
    return out[:10]


def detect_packaging_text(base: Dict[str, Any], text: str, product_name: str, brand_name: str) -> List[str]:
    candidates: List[str] = []
    for v in [product_name, brand_name, str(base.get("title", "")), str(base.get("og_title", ""))]:
        c = clean_text(v)
        if c:
            candidates.append(c)

    for sent in sentence_chunks(text):
        if len(sent) > 70:
            continue
        if any(k in sent.lower() for k in ["net wt", "oz", "ml", "fl oz", "servings", "whole bean", "serum"]):
            candidates.append(sent)
    return split_candidates(" | ".join(candidates))[:12]


def image_evidence(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    urls = base.get("image_urls") or []
    if not isinstance(urls, list):
        return out
    for idx, raw in enumerate(urls[:20]):
        url = str(raw).strip()
        if not url:
            continue
        low = url.lower()
        confidence = 0.55
        if any(k in low for k in ["front", "hero", "main", "primary"]):
            confidence = 0.8
        elif any(k in low for k in ["angle", "detail", "label"]):
            confidence = 0.72
        out.append(
            {
                "url": url,
                "source": "scout.image_urls",
                "confidence": round(confidence, 2),
                "rank": idx + 1,
            }
        )
    return out


def confidence_for(value: Any, *, min_items: int = 1) -> float:
    if isinstance(value, list):
        size = len([x for x in value if str(x).strip()])
        if size >= max(3, min_items):
            return 0.82
        if size >= min_items:
            return 0.62
        return 0.25
    text = str(value or "").strip()
    if not text:
        return 0.2
    if len(text) >= 16:
        return 0.86
    if len(text) >= 6:
        return 0.64
    return 0.4


def enrich_scout(base: Dict[str, Any]) -> Dict[str, Any]:
    scout = dict(base)
    brand_name, product_name = infer_brand_product(scout)
    corpus = text_corpus(scout)
    product_category, product_type = detect_category_and_type(corpus)
    price = detect_price(corpus)
    variants = detect_variants(corpus)
    claims = detect_claims(corpus)
    ingredients_specs = detect_ingredients_specs(corpus)
    packaging = detect_packaging_text(scout, corpus, product_name, brand_name)
    evidence = image_evidence(scout)

    field_confidence = {
        "product_name": confidence_for(product_name),
        "brand_name": confidence_for(brand_name),
        "product_category": confidence_for(product_category),
        "product_type": confidence_for(product_type),
        "price": confidence_for(price),
        "variants": confidence_for(variants, min_items=1),
        "claims_benefits": confidence_for(claims, min_items=1),
        "ingredients_materials_specs": confidence_for(ingredients_specs, min_items=1),
        "visible_packaging_text_candidates": confidence_for(packaging, min_items=2),
        "image_evidence": confidence_for(evidence, min_items=1),
    }

    warnings: List[str] = []
    for field, score in field_confidence.items():
        if score < 0.5:
            warnings.append(f"low_confidence:{field}")
    if scout.get("degraded_mode", False):
        warnings.append("degraded_mode_source:html_heuristics_only")
    if not claims:
        warnings.append("no_claims_detected")
    if not ingredients_specs:
        warnings.append("no_ingredients_or_specs_detected")

    scout.update(
        {
            "product_name": product_name,
            "brand_name": brand_name,
            "product_category": product_category,
            "product_type": product_type,
            "price": price or "unknown",
            "variants": variants,
            "claims_benefits": claims,
            "ingredients_materials_specs": ingredients_specs,
            "visible_packaging_text_candidates": packaging,
            "image_evidence": evidence,
            "field_confidence": field_confidence,
            "extraction_warnings": warnings,
        }
    )
    return scout


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enrich scout.json with structured extraction fields")
    p.add_argument("--in", dest="input_path", required=True, help="Input scout.json path")
    p.add_argument("--out", dest="output_path", help="Output path (default: overwrite input)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_path).resolve()
    output_path = Path(args.output_path).resolve() if args.output_path else input_path
    payload = enrich_scout(load_json(input_path))
    dump_json(output_path, payload)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
