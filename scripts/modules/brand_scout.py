#!/usr/bin/env python3
"""Module entrypoint: brand-scout -> scout.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packet_utils import dump_json, load_json
from scout_structured import enrich_scout

ROOT = Path(__file__).resolve().parents[2]
SCOUT_URL = ROOT / "scripts" / "scout-url.sh"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run brand-scout module and write scout.json")
    p.add_argument("--url", help="Product URL to scout")
    p.add_argument("--scout-json", help="Base scout JSON to enrich")
    p.add_argument("--packet", help="Packet directory (writes <packet>/scout.json)")
    p.add_argument("--out", help="Output scout.json path")
    return p.parse_args()


def resolve_out(args: argparse.Namespace) -> Path:
    if args.out:
        return Path(args.out).resolve()
    if args.packet:
        return Path(args.packet).resolve() / "scout.json"
    raise SystemExit("error: provide --out or --packet")


def main() -> int:
    args = parse_args()
    out = resolve_out(args)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.scout_json:
        base = load_json(Path(args.scout_json).resolve())
    elif args.url:
        proc = subprocess.run([str(SCOUT_URL), "--url", args.url], check=True, text=True, capture_output=True)
        base = json.loads(proc.stdout)
    else:
        raise SystemExit("error: provide --url or --scout-json")

    dump_json(out, enrich_scout(base))
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
