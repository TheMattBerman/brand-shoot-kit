#!/usr/bin/env python3
"""Run Brand Shoot Kit from product URL or prebuilt scout JSON.

This orchestrator keeps the current stack simple and deterministic:
1) collect scout evidence (URL fetch or provided JSON)
2) derive a packet config with conservative defaults
3) generate the packet using create-shoot-packet.py
4) optionally validate packet structure
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
CREATE_PACKET = ROOT / "scripts" / "create-shoot-packet.py"
SCOUT_URL = ROOT / "scripts" / "scout-url.sh"
VALIDATE_PACKET = ROOT / "scripts" / "validate-packet.py"


def slug(value: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in value)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "unknown"


def clean_text(value: str) -> str:
    return " ".join((value or "").replace("|", " ").split()).strip()


def infer_brand_and_product(scout: Dict[str, Any], fallback_url: str) -> Tuple[str, str]:
    title = clean_text(scout.get("og_title") or scout.get("title") or "")
    h1 = ""
    h1_list = scout.get("h1") or []
    if isinstance(h1_list, list) and h1_list:
        h1 = clean_text(str(h1_list[0]))

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

    if h1 and len(h1) >= 3:
        if not product:
            product = h1
        elif len(h1) > len(product):
            product = h1

    if not brand:
        url = fallback_url or scout.get("url", "")
        host = url.split("//")[-1].split("/")[0].split(":")[0]
        brand = host.replace("www.", "").split(".")[0].replace("-", " ").title() if host else "Unknown Brand"

    return brand or "Unknown Brand", product or "Unknown Product"


def top_images(scout: Dict[str, Any], limit: int = 5) -> List[str]:
    images = scout.get("image_urls") or []
    if not isinstance(images, list):
        return []
    out: List[str] = []
    seen = set()
    for item in images:
        url = str(item).strip()
        if not url or url in seen:
            continue
        out.append(url)
        seen.add(url)
        if len(out) >= limit:
            break
    return out


def build_config(scout: Dict[str, Any], explicit_brand: str, explicit_product: str, url: str) -> Dict[str, Any]:
    brand, product = infer_brand_and_product(scout, url)
    if explicit_brand:
        brand = explicit_brand
    if explicit_product:
        product = explicit_product

    description = clean_text(scout.get("meta_description") or scout.get("og_description") or "")
    confidence = "medium"
    if description and len(description) > 120:
        confidence = "medium-high"

    return {
        "brand": brand,
        "product": product,
        "product_url": url or scout.get("url", "not provided"),
        "price_tier": "unknown",
        "audience": "unknown",
        "tone": "brand-consistent ecommerce",
        "palette": [],
        "product_type": "unknown",
        "must_preserve": ["package geometry", "brand mark", "primary label text"],
        "can_vary": ["camera angle", "lighting direction", "set and props"],
        "never_change": ["brand name spelling", "required claims and warnings", "product count"],
        "distortion_risks": ["label text drift", "shape distortion", "scale mismatch"],
        "accuracy_confidence": confidence,
        "recommended_direction": "Clean commerce with contextual lifestyle",
        "strategy_rationale": "Default safe direction until deeper brand scouting is available.",
        "visual_gaps": [
            {"asset": "PDP hero", "status": "Unknown", "notes": "Review current hero quality from source page", "priority": "High"},
            {"asset": "Human scale/in-use", "status": "Unknown", "notes": "Confirm if human context exists", "priority": "High"},
            {"asset": "Texture/detail proof", "status": "Unknown", "notes": "Need feature clarity asset", "priority": "Medium"},
        ],
        "source_snapshot": {
            "title": clean_text(scout.get("title", "")),
            "h1": scout.get("h1", []),
            "meta_description": description,
            "top_image_urls": top_images(scout),
            "degraded_mode": bool(scout.get("degraded_mode", True)),
        },
    }


def run_cmd(cmd: List[str], capture: bool = False) -> str:
    result = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Brand Shoot Kit from URL/scout JSON to packet")
    parser.add_argument("--url", help="Product URL to scout")
    parser.add_argument("--scout-json", help="Path to pre-generated scout JSON (skip URL fetch)")
    parser.add_argument("--brand", help="Override inferred brand name")
    parser.add_argument("--product", help="Override inferred product name")
    parser.add_argument("--out", help="Packet output directory (default: output/<brand>/<product>/<today>)")
    parser.add_argument("--workdir", default="output", help="Base output dir when --out is not provided")
    parser.add_argument("--save-config", help="Optional path to write derived config JSON")
    parser.add_argument("--skip-validate", action="store_true", help="Skip packet structure validation")
    args = parser.parse_args()

    if not args.url and not args.scout_json:
        print("error: provide --url or --scout-json", file=sys.stderr)
        return 2

    if args.scout_json:
        with open(args.scout_json, "r", encoding="utf-8") as f:
            scout = json.load(f)
    else:
        scout_output = run_cmd([str(SCOUT_URL), "--url", args.url], capture=True)
        scout = json.loads(scout_output)

    config = build_config(scout, args.brand or "", args.product or "", args.url or scout.get("url", ""))

    packet_out = args.out
    if not packet_out:
        today = date.today().isoformat()
        packet_out = os.path.join(args.workdir, slug(config["brand"]), slug(config["product"]), today)

    os.makedirs(packet_out, exist_ok=True)

    config_path = args.save_config
    if not config_path:
        config_path = os.path.join(packet_out, "config.derived.json")

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    run_cmd([str(CREATE_PACKET), "--config", config_path, "--out", packet_out])

    if not args.skip_validate:
        run_cmd([str(VALIDATE_PACKET), "--packet", packet_out])

    print(packet_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
