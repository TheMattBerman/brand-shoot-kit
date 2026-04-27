#!/usr/bin/env python3
"""Deterministic channel export packaging for Brand Shoot Kit."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from packet_utils import dump_json, ensure_packet_dir, load_json, parse_export_map, slug

DEFAULT_INCLUDE = {"pass", "manual_review"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Package generated images into channel export folders")
    p.add_argument("--packet", required=True, help="Path to packet directory")
    p.add_argument("--generation-manifest", help="Path to generation manifest")
    p.add_argument("--qa-results", help="Path to qa results JSON")
    p.add_argument("--reroll-manifest", help="Path to reroll-manifest.json")
    p.add_argument("--out", help="Export root directory (default: <packet>/assets/exports/<run-id>)")
    p.add_argument(
        "--include-status",
        default="pass,manual_review",
        help="Comma separated statuses to include (default: pass,manual_review)",
    )
    return p.parse_args()


def resolve_generation(packet_dir: Path, override: str | None) -> Path:
    if override:
        path = Path(override).resolve()
    else:
        path = packet_dir / "assets" / "generated" / "generation-manifest.json"
    if not path.exists():
        raise SystemExit(f"error: generation manifest not found: {path}")
    return path


def resolve_qa(packet_dir: Path, override: str | None) -> Path:
    if override:
        path = Path(override).resolve()
    else:
        path = packet_dir / "assets" / "generated" / "qa-results.json"
    if not path.exists():
        raise SystemExit(f"error: qa results not found: {path}")
    return path


def resolve_reroll(packet_dir: Path, override: str | None) -> Path | None:
    if override:
        path = Path(override).resolve()
        if not path.exists():
            raise SystemExit(f"error: reroll manifest not found: {path}")
        return path
    path = packet_dir / "assets" / "generated" / "reroll-manifest.json"
    return path if path.exists() else None


def index_qa_results(qa_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in qa_results.get("results", []):
        out[str(item.get("asset_id"))] = item
    return out


def index_reroll(reroll: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in reroll.get("shots", []):
        out[str(item.get("asset_id"))] = item
    return out


def decision_for_asset(qa_status: str, reroll_status: str, record_status: str) -> str:
    if record_status in {"missing-source"} or reroll_status == "reroll_exhausted":
        return "reject"
    if qa_status == "pass" or reroll_status == "pass_after_reroll":
        return "approve"
    if qa_status in {"fail", "manual_review"}:
        return "reroll"
    return "reroll"


def channels_for_shot(shot_name: str, export_map: Dict[str, str], use_case: str) -> List[str]:
    raw = export_map.get(shot_name, use_case)
    parts = [p.strip() for p in raw.replace("/", ",").split(",") if p.strip()]
    if not parts:
        parts = [use_case or "unmapped"]
    return parts


def main() -> int:
    args = parse_args()
    packet_dir = Path(args.packet).resolve()
    ensure_packet_dir(packet_dir)

    generation_path = resolve_generation(packet_dir, args.generation_manifest)
    qa_path = resolve_qa(packet_dir, args.qa_results)
    reroll_path = resolve_reroll(packet_dir, args.reroll_manifest)

    generation = load_json(generation_path)
    qa_results = load_json(qa_path)
    qa_by_asset = index_qa_results(qa_results)
    reroll = load_json(reroll_path) if reroll_path else {}
    reroll_by_asset = index_reroll(reroll)

    include_statuses = {x.strip() for x in args.include_status.split(",") if x.strip()} or set(DEFAULT_INCLUDE)

    export_map = parse_export_map(packet_dir / "06-export-map.md")

    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"export-{run_stamp}"
    out_root = Path(args.out).resolve() if args.out else packet_dir / "assets" / "exports" / run_id
    out_root.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    copied = 0
    decision_counts = {"approve": 0, "reroll": 0, "reject": 0}
    qa_counts: Dict[str, int] = {}
    reroll_counts: Dict[str, int] = {}

    for entry in generation.get("entries", []):
        asset_id = str(entry.get("asset_id"))
        shot_name = str(entry.get("shot_name", asset_id))
        image_path = Path(entry.get("image_path", ""))
        qa = qa_by_asset.get(asset_id, {})
        status = qa.get("status", "unscored")
        reroll_status = str(reroll_by_asset.get(asset_id, {}).get("final_status", "not_run"))
        qa_counts[str(status)] = qa_counts.get(str(status), 0) + 1
        reroll_counts[reroll_status] = reroll_counts.get(reroll_status, 0) + 1

        if status not in include_statuses:
            decision = decision_for_asset(str(status), reroll_status, "skipped-status")
            decision_counts[decision] += 1
            records.append(
                {
                    "asset_id": asset_id,
                    "shot_name": shot_name,
                    "status": "skipped-status",
                    "qa_status": status,
                    "reroll_status": reroll_status,
                    "decision": decision,
                    "source": str(image_path),
                    "outputs": [],
                    "notes": "excluded by include-status filter",
                }
            )
            continue

        if not image_path.exists():
            decision = decision_for_asset(str(status), reroll_status, "missing-source")
            decision_counts[decision] += 1
            records.append(
                {
                    "asset_id": asset_id,
                    "shot_name": shot_name,
                    "status": "missing-source",
                    "qa_status": status,
                    "reroll_status": reroll_status,
                    "decision": decision,
                    "source": str(image_path),
                    "outputs": [],
                    "notes": "source image missing",
                }
            )
            continue

        channels = channels_for_shot(shot_name, export_map, str(entry.get("use_case", "unmapped")))
        outputs = []
        ext = image_path.suffix.lower() or ".png"

        for channel in channels:
            channel_slug = slug(channel)
            dest_dir = out_root / channel_slug
            dest_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{channel_slug}__{asset_id}__{slug(shot_name)}__{str(entry.get('ratio', 'unknown')).replace(':', 'x')}{ext}"
            dest = dest_dir / filename
            shutil.copy2(image_path, dest)
            copied += 1
            outputs.append(
                {
                    "channel": channel,
                    "path": str(dest),
                    "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                }
            )

        decision = decision_for_asset(str(status), reroll_status, "packaged")
        decision_counts[decision] += 1
        records.append(
            {
                "asset_id": asset_id,
                "shot_name": shot_name,
                "status": "packaged",
                "qa_status": status,
                "reroll_status": reroll_status,
                "decision": decision,
                "source": str(image_path),
                "ratio": entry.get("ratio", "unknown"),
                "outputs": outputs,
                "notes": "deterministic copy packaging",
            }
        )

    manifest = {
        "run": {
            "run_id": run_id,
            "timestamp_utc": run_stamp,
            "packet_dir": str(packet_dir),
            "generation_manifest": str(generation_path),
            "qa_results": str(qa_path),
            "reroll_manifest": str(reroll_path) if reroll_path else None,
            "include_status": sorted(include_statuses),
            "export_root": str(out_root),
        },
        "summary": {
            "total_assets": len(generation.get("entries", [])),
            "copied_files": copied,
            "packaged_assets": sum(1 for r in records if r["status"] == "packaged"),
            "skipped_assets": sum(1 for r in records if r["status"] != "packaged"),
            "qa_status_counts": qa_counts,
            "reroll_status_counts": reroll_counts,
            "decision_summary": decision_counts,
        },
        "records": records,
    }

    out_manifest = out_root / "export-manifest.json"
    dump_json(out_manifest, manifest)
    print(str(out_manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
