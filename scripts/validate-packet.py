#!/usr/bin/env python3
import argparse
import os
import sys

DOCS = [
    "00-brand-analysis.md",
    "01-visual-gap-audit.md",
    "02-shoot-strategy.md",
    "03-shot-list.md",
    "04-generation-prompts.md",
    "05-qa-report.md",
    "06-export-map.md",
]
ASSETS = ["pdp", "lifestyle", "model", "seasonal", "social", "email", "marketplace"]
MEMORY = ["visual-profile.md", "product-shot-memory.md", "assets.md"]
ARTIFACTS = ["scout.json", "preservation.json", "visual-gaps.json", "shoot-plan.json", "prompts.json"]


def check(path: str, is_dir: bool = False) -> bool:
    return os.path.isdir(path) if is_dir else os.path.isfile(path)


def main() -> int:
    p = argparse.ArgumentParser(description="Validate Brand Shoot packet structure")
    p.add_argument("--packet", required=True, help="Path to packet directory")
    args = p.parse_args()

    packet = args.packet
    missing = []
    for d in DOCS:
        fp = os.path.join(packet, d)
        if not check(fp):
            missing.append(fp)

    for a in ASSETS:
        ad = os.path.join(packet, "assets", a)
        if not check(ad, is_dir=True):
            missing.append(ad)

    for m in MEMORY:
        mp = os.path.join(packet, "memory", m)
        if not check(mp):
            missing.append(mp)

    for a in ARTIFACTS:
        ap = os.path.join(packet, a)
        if not check(ap):
            missing.append(ap)

    if missing:
        print("Missing required packet paths:")
        for m in missing:
            print(f"- {m}")
        return 1

    print(f"Packet valid: {packet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
