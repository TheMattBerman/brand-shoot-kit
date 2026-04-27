#!/usr/bin/env python3
"""Module entrypoint: qa-reroll -> reroll-manifest.json (and optional QA refresh)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QA_SCRIPT = ROOT / "scripts" / "qa-images.py"
REROLL_SCRIPT = ROOT / "scripts" / "reroll-failed.py"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run qa-reroll module on packet artifacts")
    p.add_argument("--packet", required=True, help="Packet directory")
    p.add_argument("--run-qa", action="store_true", help="Refresh qa-results.json before reroll")
    p.add_argument("--threshold", default="80.0", help="QA threshold when --run-qa is used")
    p.add_argument("--max-attempts", default="2", help="Max reroll attempts")
    p.add_argument("--live", action="store_true", help="Use live reroll mode")
    return p.parse_args()


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    args = parse_args()
    packet = str(Path(args.packet).resolve())
    if args.run_qa:
        run_cmd([str(QA_SCRIPT), "--packet", packet, "--threshold", str(args.threshold)])

    reroll_cmd = [str(REROLL_SCRIPT), "--packet", packet, "--max-attempts", str(args.max_attempts)]
    if args.live:
        reroll_cmd.append("--live")
    run_cmd(reroll_cmd)
    print(str(Path(packet) / "assets" / "generated" / "reroll-manifest.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
