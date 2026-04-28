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
    if any(k in t for k in ["cleaning", "multi-surface", "dish soap", "laundry", "refill", "spray"]):
        return "cleaning", "cleaning kit"
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


def _safe_json_loads(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return None


def _coerce_jsonish(value: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if isinstance(value, dict):
        out.append(value)
        return out
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str):
                parsed = _safe_json_loads(item)
                if isinstance(parsed, dict):
                    out.append(parsed)
                elif isinstance(parsed, list):
                    out.extend([x for x in parsed if isinstance(x, dict)])
        return out
    if isinstance(value, str):
        parsed = _safe_json_loads(value)
        if isinstance(parsed, dict):
            out.append(parsed)
        elif isinstance(parsed, list):
            out.extend([x for x in parsed if isinstance(x, dict)])
    return out


def _flatten_items(value: Any) -> List[Dict[str, Any]]:
    items = _coerce_jsonish(value)
    out: List[Dict[str, Any]] = []
    stack = list(items)
    while stack:
        item = stack.pop(0)
        out.append(item)
        graph = item.get("@graph")
        if isinstance(graph, list):
            for row in graph:
                if isinstance(row, dict):
                    stack.append(row)
    return out


def _json_ld_products(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    for key in ["json_ld", "jsonld", "structured_data", "ld_json"]:
        collected.extend(_flatten_items(base.get(key)))

    out: List[Dict[str, Any]] = []
    for item in collected:
        t = item.get("@type")
        type_text = ""
        if isinstance(t, list):
            type_text = " ".join(str(x) for x in t)
        else:
            type_text = str(t or "")
        low = type_text.lower()
        if "product" in low or "productgroup" in low:
            out.append(item)
    return out


def _possible_product_json(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    keys = [
        "shopify_product",
        "shopify_product_json",
        "product_json",
        "product",
        "shopify",
        "shopify_payload",
    ]
    for key in keys:
        out.extend(_coerce_jsonish(base.get(key)))
    return out


def _shopify_metafields(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for key in ["metafields", "shopify_metafields", "product_metafields"]:
        value = base.get(key)
        if isinstance(value, dict):
            out.append(value)
        elif isinstance(value, list):
            out.extend([x for x in value if isinstance(x, dict)])
        elif isinstance(value, str):
            parsed = _safe_json_loads(value)
            if isinstance(parsed, dict):
                out.append(parsed)
            elif isinstance(parsed, list):
                out.extend([x for x in parsed if isinstance(x, dict)])
    return out


def _extract_shopify_price(product: Dict[str, Any]) -> str:
    for key in ["price", "price_min", "compare_at_price", "price_varies"]:
        if key in product:
            raw = product.get(key)
            text = clean_text(str(raw))
            if text and text not in {"true", "false"}:
                if re.fullmatch(r"\d+(?:\.\d{2})?", text):
                    return f"${text}"
                return text

    variants = product.get("variants")
    if isinstance(variants, list):
        for item in variants:
            if not isinstance(item, dict):
                continue
            price = clean_text(str(item.get("price", "")))
            if not price:
                continue
            if re.fullmatch(r"\d+(?:\.\d{2})?", price):
                return f"${price}"
            if re.search(r"\$", price):
                return price
    return ""


def _extract_jsonld_price(products: List[Dict[str, Any]]) -> str:
    for product in products:
        offers = product.get("offers")
        offer_rows = offers if isinstance(offers, list) else [offers]
        for offer in offer_rows:
            if not isinstance(offer, dict):
                continue
            amount = clean_text(str(offer.get("price", "")))
            currency = clean_text(str(offer.get("priceCurrency", "")))
            if not amount:
                continue
            if re.fullmatch(r"\d+(?:\.\d{2})?", amount):
                symbol = "$" if currency.upper() in {"", "USD"} else f"{currency.upper()} "
                return f"{symbol}{amount}"
            return amount
    return ""


def _extract_variants_from_shopify(product: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    variants = product.get("variants")
    if isinstance(variants, list):
        for item in variants:
            if not isinstance(item, dict):
                continue
            for key in ["title", "name", "option1", "option2", "option3"]:
                val = clean_text(str(item.get(key, "")))
                if val and val.lower() not in {"default title", "default"}:
                    out.append(val)
    options = product.get("options")
    if isinstance(options, list):
        for item in options:
            if isinstance(item, dict):
                values = item.get("values")
                if isinstance(values, list):
                    out.extend(clean_text(str(v)) for v in values if clean_text(str(v)))
            else:
                val = clean_text(str(item))
                if val:
                    out.append(val)
    return split_candidates(" | ".join(out))[:12]


def _extract_variants_from_jsonld(products: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for product in products:
        for key in ["sku", "color", "size", "name"]:
            val = clean_text(str(product.get(key, "")))
            if key == "name":
                if val and len(val) < 80:
                    out.append(val)
            elif val:
                out.append(val)
        variants = product.get("hasVariant")
        if isinstance(variants, list):
            for var in variants:
                if isinstance(var, dict):
                    name = clean_text(str(var.get("name", "")))
                    if name:
                        out.append(name)
    return split_candidates(" | ".join(out))[:12]


def _extract_ingredients_specs_from_structured(
    products_jsonld: List[Dict[str, Any]],
    shopify_products: List[Dict[str, Any]],
    metafields: List[Dict[str, Any]],
) -> List[str]:
    out: List[str] = []

    for product in products_jsonld:
        for key in ["description", "additionalProperty", "material", "category"]:
            value = product.get(key)
            if isinstance(value, list):
                for row in value:
                    if isinstance(row, dict):
                        nv = clean_text(f"{row.get('name', '')}: {row.get('value', '')}")
                        if nv and len(nv) >= 4:
                            out.append(nv)
                    else:
                        text = clean_text(str(row))
                        if text:
                            out.append(text)
            elif isinstance(value, dict):
                nv = clean_text(f"{value.get('name', '')}: {value.get('value', '')}")
                if nv:
                    out.append(nv)
            else:
                text = clean_text(str(value))
                if text and any(k in text.lower() for k in ["ingredient", "spec", "net wt", "serving", "material", "roast", "oz", "ml"]):
                    out.append(text)

    for product in shopify_products:
        for key in ["description", "body_html", "description_html", "subtitle"]:
            text = clean_text(str(product.get(key, "")))
            if not text:
                continue
            if any(k in text.lower() for k in ["ingredient", "spec", "serving", "net wt", "oz", "ml", "roast", "origin", "material"]):
                out.append(text)

    for meta in metafields:
        for key, value in meta.items():
            key_text = clean_text(str(key)).lower()
            if isinstance(value, dict):
                for k2, v2 in value.items():
                    row = clean_text(f"{k2}: {v2}")
                    if row and any(t in (key_text + " " + row.lower()) for t in ["ingredient", "spec", "serving", "net wt", "origin", "roast", "material"]):
                        out.append(row)
            elif isinstance(value, list):
                for row in value:
                    text = clean_text(str(row))
                    if text and any(t in (key_text + " " + text.lower()) for t in ["ingredient", "spec", "serving", "net wt", "origin", "roast", "material"]):
                        out.append(text)
            else:
                text = clean_text(str(value))
                if text and any(t in (key_text + " " + text.lower()) for t in ["ingredient", "spec", "serving", "net wt", "origin", "roast", "material"]):
                    out.append(text)

    return split_candidates(" | ".join(out))[:14]


def _extract_packaging_from_structured(
    *,
    products_jsonld: List[Dict[str, Any]],
    shopify_products: List[Dict[str, Any]],
    metafields: List[Dict[str, Any]],
    product_name: str,
    brand_name: str,
) -> List[str]:
    out: List[str] = [product_name, brand_name]

    for product in products_jsonld:
        for key in ["name", "sku", "brand", "gtin", "category"]:
            value = product.get(key)
            if isinstance(value, dict):
                text = clean_text(str(value.get("name", "")))
            else:
                text = clean_text(str(value))
            if text:
                out.append(text)

    for product in shopify_products:
        for key in ["title", "vendor", "product_type", "tags", "sku"]:
            value = product.get(key)
            if isinstance(value, list):
                for item in value:
                    text = clean_text(str(item))
                    if text:
                        out.append(text)
            else:
                text = clean_text(str(value))
                if text:
                    out.append(text)

    for meta in metafields:
        stack: List[Tuple[str, Any]] = [(str(k), v) for k, v in meta.items()]
        while stack:
            key, value = stack.pop(0)
            key_text = clean_text(str(key)).lower()
            if isinstance(value, dict):
                for k2, v2 in value.items():
                    stack.append((f"{key}.{k2}", v2))
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    stack.append((f"{key}[{idx}]", item))
            else:
                text = clean_text(str(value))
                if not text:
                    continue
                if any(k in key_text for k in ["pack", "label", "title", "net", "weight", "size", "volume", "artwork"]):
                    out.append(text)

    return split_candidates(" | ".join(out))[:16]


def extract_structured_product_fields(base: Dict[str, Any], product_name: str, brand_name: str) -> Dict[str, Any]:
    jsonld_products = _json_ld_products(base)
    shopify_products = _possible_product_json(base)
    metafields = _shopify_metafields(base)

    price = ""
    variants: List[str] = []
    ingredients_specs: List[str] = []
    packaging: List[str] = []
    source_hints: List[str] = []

    if jsonld_products:
        price = _extract_jsonld_price(jsonld_products)
        variants = _extract_variants_from_jsonld(jsonld_products)
        ingredients_specs = _extract_ingredients_specs_from_structured(jsonld_products, [], [])
        packaging = _extract_packaging_from_structured(
            products_jsonld=jsonld_products,
            shopify_products=[],
            metafields=[],
            product_name=product_name,
            brand_name=brand_name,
        )
        source_hints.append("json-ld")

    if shopify_products:
        if not price:
            for product in shopify_products:
                candidate = _extract_shopify_price(product)
                if candidate:
                    price = candidate
                    break
        shopify_variants: List[str] = []
        for product in shopify_products:
            shopify_variants.extend(_extract_variants_from_shopify(product))
        if shopify_variants:
            variants = split_candidates(" | ".join(variants + shopify_variants))[:12]

        rich_specs = _extract_ingredients_specs_from_structured([], shopify_products, [])
        if rich_specs:
            ingredients_specs = split_candidates(" | ".join(ingredients_specs + rich_specs))[:14]

        rich_packaging = _extract_packaging_from_structured(
            products_jsonld=[],
            shopify_products=shopify_products,
            metafields=[],
            product_name=product_name,
            brand_name=brand_name,
        )
        if rich_packaging:
            packaging = split_candidates(" | ".join(packaging + rich_packaging))[:16]

        source_hints.append("shopify-product-json")

    if metafields:
        meta_specs = _extract_ingredients_specs_from_structured([], [], metafields)
        if meta_specs:
            ingredients_specs = split_candidates(" | ".join(ingredients_specs + meta_specs))[:14]
        meta_packaging = _extract_packaging_from_structured(
            products_jsonld=[],
            shopify_products=[],
            metafields=metafields,
            product_name=product_name,
            brand_name=brand_name,
        )
        if meta_packaging:
            packaging = split_candidates(" | ".join(packaging + meta_packaging))[:16]
        source_hints.append("shopify-metafields")

    return {
        "price": price,
        "variants": variants,
        "ingredients_specs": ingredients_specs,
        "packaging": packaging,
        "sources": source_hints,
        "has_structured": bool(jsonld_products or shopify_products or metafields),
    }


def _structured_overrides(base: Dict[str, Any]) -> Dict[str, Any]:
    """Pull values from base['structured_product'] for use as preferred extractions."""
    sp = base.get("structured_product") or {}
    if not isinstance(sp, dict) or not sp:
        return {}
    return {
        "brand_name": sp.get("brand") or "",
        "product_name": sp.get("product_name") or "",
        "price": sp.get("price") or "",
        "variants": list(sp.get("variants") or []),
        "claims_benefits": list(sp.get("claims") or []),
        "ingredients_materials_specs": list(sp.get("ingredients") or []),
        "visible_packaging_text_candidates": (
            [sp["packaging_description"]] if sp.get("packaging_description") else []
        ),
        "product_category": sp.get("category_hint") or "",
    }


def enrich_scout(base: Dict[str, Any]) -> Dict[str, Any]:
    scout = dict(base)
    brand_name, product_name = infer_brand_product(scout)
    corpus = text_corpus(scout)
    product_category, product_type = detect_category_and_type(corpus)

    structured = extract_structured_product_fields(scout, product_name, brand_name)
    price = structured["price"] or detect_price(corpus)
    variants = structured["variants"] or detect_variants(corpus)
    claims = detect_claims(corpus)
    ingredients_specs = structured["ingredients_specs"] or detect_ingredients_specs(corpus)
    packaging = structured["packaging"] or detect_packaging_text(scout, corpus, product_name, brand_name)
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
    if structured["has_structured"]:
        warnings.append("structured_source:" + ",".join(structured["sources"]))
    else:
        warnings.append("structured_source:none_detected_using_heuristics")
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

    # Prefer Firecrawl schema-extracted values when present.
    overrides = _structured_overrides(base)
    for field, value in overrides.items():
        if not value:
            continue
        scout[field] = value

    # Insert Firecrawl main_image_url as a high-confidence image_evidence entry.
    main_image = base.get("main_image_url")
    if main_image:
        img_evidence = scout.get("image_evidence") or []
        if not any(str(e.get("url", "")) == main_image for e in img_evidence):
            img_evidence.insert(0, {
                "url": main_image,
                "source": "firecrawl.main_image_url",
                "confidence": 0.95,
                "rank": 0,
            })
        scout["image_evidence"] = img_evidence

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
