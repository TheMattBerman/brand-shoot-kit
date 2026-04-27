#!/usr/bin/env python3
"""Create or render a Brand Shoot packet.

Modes:
1) --config + --out: build stage artifacts and render docs
2) --artifacts-dir: render docs from existing artifacts
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any, Dict, Tuple

from packet_utils import load_json
from pipeline_stages import (
    default_output_dir,
    infer_brand_and_product,
    render_packet_docs,
    save_stage_artifacts,
    stage_preservation,
    stage_prompts,
    stage_shoot_plan,
    stage_visual_gaps,
)


REQUIRED_ARTIFACTS = [
    "scout.json",
    "preservation.json",
    "visual-gaps.json",
    "shoot-plan.json",
    "prompts.json",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create Brand Shoot packet docs from config or artifacts")
    p.add_argument("--config", help="Path to packet config JSON")
    p.add_argument("--artifacts-dir", help="Directory containing stage artifacts")
    p.add_argument("--out", help="Output packet directory (required with --config)")
    return p.parse_args()


def infer_identity_from_config(cfg: Dict[str, Any], scout: Dict[str, Any]) -> Tuple[str, str, str]:
    brand = str(cfg.get("brand") or "").strip()
    product = str(cfg.get("product") or "").strip()
    product_url = str(cfg.get("product_url") or scout.get("url") or "not provided")
    if not brand or not product:
        inferred_brand, inferred_product = infer_brand_and_product(scout, product_url)
        brand = brand or inferred_brand
        product = product or inferred_product
    return brand, product, product_url


def load_required_artifacts(root: Path) -> Dict[str, Dict[str, Any]]:
    artifacts: Dict[str, Dict[str, Any]] = {}
    missing = []
    for name in REQUIRED_ARTIFACTS:
        path = root / name
        if not path.exists():
            missing.append(str(path))
            continue
        artifacts[name] = load_json(path)

    if missing:
        raise SystemExit(f"error: missing artifacts: {missing}")

    return artifacts


def build_from_config(config_path: Path, out_dir: Path) -> None:
    cfg = load_json(config_path)
    scout = dict(cfg.get("scout") or {})
    if not scout:
        scout = {
            "url": cfg.get("product_url", "not provided"),
            "title": cfg.get("product", "Unknown Product"),
            "meta_description": cfg.get("source_snapshot", {}).get("meta_description", ""),
            "og_title": cfg.get("product", "Unknown Product"),
            "og_description": cfg.get("source_snapshot", {}).get("meta_description", ""),
            "h1": cfg.get("source_snapshot", {}).get("h1", []),
            "image_urls": cfg.get("source_snapshot", {}).get("top_image_urls", []),
            "degraded_mode": True,
            "note": "Derived scout from config for backward compatibility",
        }

    brand, product, product_url = infer_identity_from_config(cfg, scout)

    preservation = stage_preservation(
        scout,
        product=product,
        explicit_product_type=cfg.get("product_type"),
        explicit_tone=cfg.get("tone"),
        explicit_audience=cfg.get("audience"),
    )

    if cfg.get("must_preserve"):
        preservation["must_preserve"] = [str(x) for x in cfg.get("must_preserve", [])]
    if cfg.get("can_vary"):
        preservation["can_vary"] = [str(x) for x in cfg.get("can_vary", [])]
    if cfg.get("never_change"):
        preservation["never_change"] = [str(x) for x in cfg.get("never_change", [])]
    if cfg.get("distortion_risks"):
        preservation["distortion_risks"] = [str(x) for x in cfg.get("distortion_risks", [])]
    if cfg.get("accuracy_confidence"):
        preservation["accuracy_confidence"] = str(cfg.get("accuracy_confidence"))

    visual_gaps = stage_visual_gaps(scout, preservation)
    if cfg.get("visual_gaps"):
        visual_gaps["rows"] = [dict(x) for x in cfg.get("visual_gaps", [])]

    shoot_plan = stage_shoot_plan(
        scout,
        preservation,
        visual_gaps,
        recommended_direction=cfg.get("recommended_direction"),
        strategy_rationale=cfg.get("strategy_rationale"),
        explicit_shots=cfg.get("shots"),
    )

    prompts = stage_prompts(scout, preservation, shoot_plan, brand=brand, product=product)

    save_stage_artifacts(
        out_dir,
        scout=scout,
        preservation=preservation,
        visual_gaps=visual_gaps,
        shoot_plan=shoot_plan,
        prompts=prompts,
    )

    render_packet_docs(
        out_dir,
        brand=brand,
        product=product,
        product_url=product_url,
        scout=scout,
        preservation=preservation,
        visual_gaps=visual_gaps,
        shoot_plan=shoot_plan,
        prompts=prompts,
    )


def render_from_artifacts(artifacts_dir: Path, out_dir: Path) -> None:
    artifacts = load_required_artifacts(artifacts_dir)
    scout = artifacts["scout.json"]
    preservation = artifacts["preservation.json"]
    visual_gaps = artifacts["visual-gaps.json"]
    shoot_plan = artifacts["shoot-plan.json"]
    prompts = artifacts["prompts.json"]

    brand, product = infer_brand_and_product(scout, str(scout.get("url", "")))
    product_url = str(scout.get("url", "not provided"))

    render_packet_docs(
        out_dir,
        brand=brand,
        product=product,
        product_url=product_url,
        scout=scout,
        preservation=preservation,
        visual_gaps=visual_gaps,
        shoot_plan=shoot_plan,
        prompts=prompts,
    )


def main() -> None:
    args = parse_args()

    if not args.config and not args.artifacts_dir:
        raise SystemExit("error: provide --config or --artifacts-dir")

    if args.config and args.artifacts_dir:
        raise SystemExit("error: choose one mode: --config or --artifacts-dir")

    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            raise SystemExit(f"error: config not found: {config_path}")
        if args.out:
            out_dir = Path(args.out).resolve()
        else:
            cfg = load_json(config_path)
            scout = dict(cfg.get("scout") or {})
            brand = str(cfg.get("brand") or "").strip() or infer_brand_and_product(scout, str(cfg.get("product_url", "")))[0]
            product = str(cfg.get("product") or "").strip() or infer_brand_and_product(scout, str(cfg.get("product_url", "")))[1]
            out_dir = default_output_dir(Path("output").resolve(), brand, product)
        out_dir.mkdir(parents=True, exist_ok=True)
        build_from_config(config_path, out_dir)
        print(str(out_dir))
        return

    artifacts_dir = Path(args.artifacts_dir).resolve()
    if not artifacts_dir.exists():
        raise SystemExit(f"error: artifacts-dir not found: {artifacts_dir}")

    out_dir = Path(args.out).resolve() if args.out else artifacts_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    render_from_artifacts(artifacts_dir, out_dir)
    print(str(out_dir))


if __name__ == "__main__":
    main()
