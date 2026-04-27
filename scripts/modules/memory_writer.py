#!/usr/bin/env python3
"""Module entrypoint: memory-writer -> packet memory markdown files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def latest_export_manifest(packet: Path) -> Path | None:
    manifests = sorted((packet / "assets" / "exports").glob("*/export-manifest.json"), key=lambda p: p.stat().st_mtime)
    return manifests[-1] if manifests else None


def safe_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(x) for x in value if str(x).strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run memory-writer module")
    p.add_argument("--packet", required=True, help="Packet directory")
    p.add_argument("--qa-results", help="Override qa-results.json")
    p.add_argument("--reroll-manifest", help="Override reroll-manifest.json")
    p.add_argument("--export-manifest", help="Override export-manifest.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    memory_dir = packet / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    qa_path = Path(args.qa_results).resolve() if args.qa_results else packet / "assets" / "generated" / "qa-results.json"
    reroll_path = (
        Path(args.reroll_manifest).resolve()
        if args.reroll_manifest
        else packet / "assets" / "generated" / "reroll-manifest.json"
    )
    export_path = Path(args.export_manifest).resolve() if args.export_manifest else latest_export_manifest(packet)

    qa = load_json(qa_path) if qa_path.exists() else {"summary": {}, "results": []}
    reroll = load_json(reroll_path) if reroll_path.exists() else {"summary": {}, "shots": []}
    export = load_json(export_path) if export_path and export_path.exists() else {"summary": {}, "records": []}

    failed_reasons: Dict[str, int] = {}
    for row in qa.get("results", []):
        for reason in safe_list(row.get("reject_reasons")):
            failed_reasons[reason] = failed_reasons.get(reason, 0) + 1
    top_reasons = sorted(failed_reasons.items(), key=lambda item: item[1], reverse=True)[:5]

    visual_profile = [
        "# Visual Profile",
        "",
        f"- QA mode: {qa.get('run', {}).get('mode', 'unknown')}",
        f"- QA pass/fail/manual: {qa.get('summary', {}).get('pass', 0)}/{qa.get('summary', {}).get('fail', 0)}/{qa.get('summary', {}).get('manual_review', 0)}",
        f"- Reroll convergence: {reroll.get('summary', {}).get('pass_after_reroll', 0)} pass after reroll",
        f"- Reroll exhausted: {reroll.get('summary', {}).get('reroll_exhausted', 0)}",
        "",
        "## Repeated Failure Patterns",
    ]
    if top_reasons:
        for reason, count in top_reasons:
            visual_profile.append(f"- {reason} ({count})")
    else:
        visual_profile.append("- no recurring reject reasons recorded")

    shot_memory = [
        "# Product Shot Memory",
        "",
        "## Reroll Summary",
        f"- Eligible shots: {reroll.get('summary', {}).get('eligible_shots', 0)}",
        f"- Total attempts: {reroll.get('summary', {}).get('total_attempts', 0)}",
        f"- Convergence rate: {reroll.get('summary', {}).get('convergence_rate', 0.0)}%",
        "",
        "## Preserve In Future Runs",
        "- Keep product framing tight enough for label legibility in commerce shots.",
        "- Keep product count and package geometry fixed across lifestyle variants.",
        "- Use calmer sets when extraction confidence is low.",
    ]

    assets_md = [
        "# Assets Log",
        "",
        f"- Export packaged assets: {export.get('summary', {}).get('packaged_assets', 0)}",
        f"- Export copied files: {export.get('summary', {}).get('copied_files', 0)}",
        "",
        "## Latest Export Manifest",
        f"- Path: {str(export_path) if export_path else 'none'}",
    ]

    (memory_dir / "visual-profile.md").write_text("\n".join(visual_profile).rstrip() + "\n", encoding="utf-8")
    (memory_dir / "product-shot-memory.md").write_text("\n".join(shot_memory).rstrip() + "\n", encoding="utf-8")
    (memory_dir / "assets.md").write_text("\n".join(assets_md).rstrip() + "\n", encoding="utf-8")
    print(str(memory_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
