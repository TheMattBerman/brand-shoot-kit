#!/usr/bin/env python3
"""Module entrypoint: visual-gap-audit -> visual-gaps.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packet_utils import dump_json, load_json
from pipeline_stages import stage_visual_gaps


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run visual-gap-audit module")
    p.add_argument("--packet", required=True, help="Packet directory with scout/preservation artifacts")
    p.add_argument("--scout", help="Override scout.json path")
    p.add_argument("--preservation", help="Override preservation.json path")
    p.add_argument("--out", help="Output visual-gaps.json path (default: <packet>/visual-gaps.json)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    scout_path = Path(args.scout).resolve() if args.scout else packet / "scout.json"
    preservation_path = Path(args.preservation).resolve() if args.preservation else packet / "preservation.json"
    out = Path(args.out).resolve() if args.out else packet / "visual-gaps.json"

    scout = load_json(scout_path)
    preservation = load_json(preservation_path)
    visual_gaps = stage_visual_gaps(scout, preservation)
    dump_json(out, visual_gaps)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
