#!/usr/bin/env python3
"""Module entrypoint: export-packager -> export manifest."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCRIPT = ROOT / "scripts" / "export-packager.py"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run export-packager module")
    p.add_argument("--packet", required=True, help="Packet directory")
    p.add_argument("--out", help="Optional explicit export output directory")
    p.add_argument("--include-status", default="pass,manual_review", help="Included QA statuses")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cmd = [
        str(EXPORT_SCRIPT),
        "--packet",
        str(Path(args.packet).resolve()),
        "--include-status",
        args.include_status,
    ]
    if args.out:
        cmd += ["--out", str(Path(args.out).resolve())]
    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
