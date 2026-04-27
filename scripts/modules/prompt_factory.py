#!/usr/bin/env python3
"""Module entrypoint: prompt-factory -> prompts.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packet_utils import dump_json, load_json
from pipeline_stages import infer_brand_and_product, stage_prompts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run prompt-factory module")
    p.add_argument("--packet", required=True, help="Packet directory with stage artifacts")
    p.add_argument("--scout", help="Override scout.json path")
    p.add_argument("--preservation", help="Override preservation.json path")
    p.add_argument("--shoot-plan", help="Override shoot-plan.json path")
    p.add_argument("--brand", help="Optional brand override")
    p.add_argument("--product", help="Optional product override")
    p.add_argument("--out", help="Output prompts.json path (default: <packet>/prompts.json)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    scout_path = Path(args.scout).resolve() if args.scout else packet / "scout.json"
    preservation_path = Path(args.preservation).resolve() if args.preservation else packet / "preservation.json"
    shoot_plan_path = Path(args.shoot_plan).resolve() if args.shoot_plan else packet / "shoot-plan.json"
    out = Path(args.out).resolve() if args.out else packet / "prompts.json"

    scout = load_json(scout_path)
    preservation = load_json(preservation_path)
    shoot_plan = load_json(shoot_plan_path)
    inferred_brand, inferred_product = infer_brand_and_product(scout, str(scout.get("url", "")))
    prompts = stage_prompts(
        scout,
        preservation,
        shoot_plan,
        brand=args.brand or inferred_brand,
        product=args.product or inferred_product,
    )
    dump_json(out, prompts)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
