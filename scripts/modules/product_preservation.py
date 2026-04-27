#!/usr/bin/env python3
"""Module entrypoint: product-preservation -> preservation.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packet_utils import dump_json, load_json
from pipeline_stages import infer_brand_and_product, stage_preservation


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run product-preservation module")
    p.add_argument("--packet", required=True, help="Packet directory with scout.json")
    p.add_argument("--scout", help="Override scout.json path")
    p.add_argument("--product", help="Optional product override")
    p.add_argument("--out", help="Output preservation.json path (default: <packet>/preservation.json)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    scout_path = Path(args.scout).resolve() if args.scout else packet / "scout.json"
    out = Path(args.out).resolve() if args.out else packet / "preservation.json"

    scout = load_json(scout_path)
    _brand, inferred_product = infer_brand_and_product(scout, str(scout.get("url", "")))
    preservation = stage_preservation(scout, product=args.product or inferred_product)
    dump_json(out, preservation)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
