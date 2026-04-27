#!/usr/bin/env python3
"""Run Brand Shoot Kit from product URL or prebuilt scout JSON.

This orchestrator now writes first-class module artifacts:
- scout.json
- preservation.json
- visual-gaps.json
- shoot-plan.json
- prompts.json

You can run all stages or regenerate a single stage with --stage.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

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
from scout_structured import enrich_scout

ROOT = Path(__file__).resolve().parent.parent
SCOUT_URL = ROOT / "scripts" / "scout-url.sh"
VALIDATE_PACKET = ROOT / "scripts" / "validate-packet.py"


def run_cmd(cmd: List[str], capture: bool = False) -> str:
    result = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def load_artifact(out_dir: Path, name: str) -> Dict[str, Any]:
    path = out_dir / name
    if not path.exists():
        raise SystemExit(f"error: required artifact missing for this stage: {path}")
    return load_json(path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Brand Shoot Kit stages and packet rendering")
    p.add_argument("--url", help="Product URL to scout")
    p.add_argument("--scout-json", help="Path to pre-generated scout JSON")
    p.add_argument("--brand", help="Override inferred brand name")
    p.add_argument("--product", help="Override inferred product name")
    p.add_argument("--out", help="Packet output directory")
    p.add_argument("--workdir", default="output", help="Base output dir when --out is not provided")
    p.add_argument("--stage", choices=["all", "scout", "preservation", "visual-gaps", "shoot-plan", "prompts", "render"], default="all", help="Run full pipeline or a single stage")
    p.add_argument("--save-config", help="Optional path to write derived config JSON")
    p.add_argument("--skip-validate", action="store_true", help="Skip packet structure validation")
    return p.parse_args()


def resolve_output_dir(args: argparse.Namespace, scout: Dict[str, Any] | None) -> Path:
    if args.out:
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    if scout is None:
        raise SystemExit("error: --out is required when running stage without scout input")

    brand, product = infer_brand_and_product(scout, args.url or str(scout.get("url", "")))
    if args.brand:
        brand = args.brand
    if args.product:
        product = args.product
    out_dir = default_output_dir(Path(args.workdir).resolve(), brand, product)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def derive_identity(args: argparse.Namespace, scout: Dict[str, Any], out_dir: Path) -> Dict[str, str]:
    inferred_brand, inferred_product = infer_brand_and_product(scout, args.url or str(scout.get("url", "")))
    brand = args.brand or inferred_brand
    product = args.product or inferred_product
    product_url = args.url or str(scout.get("url", "not provided"))

    if args.save_config:
        config_path = Path(args.save_config)
    else:
        config_path = out_dir / "config.derived.json"

    payload = {
        "brand": brand,
        "product": product,
        "product_url": product_url,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def scout_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    if args.scout_json:
        return enrich_scout(load_json(Path(args.scout_json).resolve()))
    if args.url:
        scout_output = run_cmd([str(SCOUT_URL), "--url", args.url], capture=True)
        return enrich_scout(json.loads(scout_output))
    raise SystemExit("error: provide --url or --scout-json")


def run_stage(args: argparse.Namespace) -> int:
    stage = args.stage

    if stage in {"all", "scout"}:
        scout = scout_from_args(args)
        out_dir = resolve_output_dir(args, scout)
        save_stage_artifacts(out_dir, scout=scout)

        if stage == "scout":
            print(str(out_dir / "scout.json"))
            return 0
    else:
        out_dir = resolve_output_dir(args, None)
        scout = load_artifact(out_dir, "scout.json")

    identity = derive_identity(args, scout, out_dir)
    brand = identity["brand"]
    product = identity["product"]
    product_url = identity["product_url"]

    if stage in {"all", "preservation"}:
        preservation = stage_preservation(scout, product=product)
        save_stage_artifacts(out_dir, preservation=preservation)
        if stage == "preservation":
            print(str(out_dir / "preservation.json"))
            return 0
    else:
        preservation = load_artifact(out_dir, "preservation.json")

    if stage in {"all", "visual-gaps"}:
        visual_gaps = stage_visual_gaps(scout, preservation)
        save_stage_artifacts(out_dir, visual_gaps=visual_gaps)
        if stage == "visual-gaps":
            print(str(out_dir / "visual-gaps.json"))
            return 0
    else:
        visual_gaps = load_artifact(out_dir, "visual-gaps.json")

    if stage in {"all", "shoot-plan"}:
        shoot_plan = stage_shoot_plan(scout, preservation, visual_gaps)
        save_stage_artifacts(out_dir, shoot_plan=shoot_plan)
        if stage == "shoot-plan":
            print(str(out_dir / "shoot-plan.json"))
            return 0
    else:
        shoot_plan = load_artifact(out_dir, "shoot-plan.json")

    if stage in {"all", "prompts"}:
        prompts = stage_prompts(scout, preservation, shoot_plan, brand=brand, product=product)
        save_stage_artifacts(out_dir, prompts=prompts)
        if stage == "prompts":
            print(str(out_dir / "prompts.json"))
            return 0
    else:
        prompts = load_artifact(out_dir, "prompts.json")

    if stage in {"all", "render"}:
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

    if not args.skip_validate and stage in {"all", "render"}:
        run_cmd([str(VALIDATE_PACKET), "--packet", str(out_dir)])

    print(str(out_dir))
    return 0


def main() -> int:
    args = parse_args()
    return run_stage(args)


if __name__ == "__main__":
    sys.exit(main())
