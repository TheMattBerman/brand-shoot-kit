#!/usr/bin/env python3
"""Module entrypoint: shoot-director -> shoot-plan.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packet_utils import dump_json, load_json
from pipeline_stages import stage_shoot_plan


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run shoot-director module")
    p.add_argument("--packet", required=True, help="Packet directory with scout/preservation/visual-gaps artifacts")
    p.add_argument("--scout", help="Override scout.json path")
    p.add_argument("--preservation", help="Override preservation.json path")
    p.add_argument("--visual-gaps", help="Override visual-gaps.json path")
    p.add_argument("--out", help="Output shoot-plan.json path (default: <packet>/shoot-plan.json)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    scout_path = Path(args.scout).resolve() if args.scout else packet / "scout.json"
    preservation_path = Path(args.preservation).resolve() if args.preservation else packet / "preservation.json"
    visual_gaps_path = Path(args.visual_gaps).resolve() if args.visual_gaps else packet / "visual-gaps.json"
    out = Path(args.out).resolve() if args.out else packet / "shoot-plan.json"

    scout = load_json(scout_path)
    preservation = load_json(preservation_path)
    visual_gaps = load_json(visual_gaps_path)
    shoot_plan = stage_shoot_plan(scout, preservation, visual_gaps)
    dump_json(out, shoot_plan)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
