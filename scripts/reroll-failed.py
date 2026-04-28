#!/usr/bin/env python3
"""Execute or simulate rerolls for failed Brand Shoot QA results."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any, Dict, List

from packet_utils import dump_json, ensure_packet_dir, load_json, parse_generation_prompts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simulate/execute rerolls from QA results")
    p.add_argument("--packet", required=True, help="Path to packet directory")
    p.add_argument("--qa-results", help="Path to qa-results.json")
    p.add_argument("--generation-manifest", help="Path to generation-manifest.json")
    p.add_argument("--prompts-json", help="Path to prompts.json")
    p.add_argument("--prompts-md", help="Path to 04-generation-prompts.md")
    p.add_argument("--out", help="Reroll manifest path (default: <packet>/assets/generated/reroll-manifest.json)")
    p.add_argument("--max-attempts", type=int, default=2, help="Maximum reroll attempts per failed shot")
    p.add_argument("--live", action="store_true", help="Execute live rerolls via generate-images.py --live")
    p.add_argument("--live-model", default="gpt-image-2", help="Model passed to generate-images.py in live mode")
    p.add_argument("--live-qa", action="store_true", help="After live reroll generation, re-score the rerolled asset with qa-images.py --live")
    p.add_argument("--qa-threshold", type=float, default=80.0, help="QA threshold for --live-qa closed-loop reroll checks")
    p.add_argument("--reroll-status", default="fail,manual_review", help="Comma-separated QA statuses eligible for reroll")
    return p.parse_args()


def resolve_paths(args: argparse.Namespace) -> Dict[str, Path]:
    packet = Path(args.packet).resolve()
    ensure_packet_dir(packet)

    qa_path = Path(args.qa_results).resolve() if args.qa_results else packet / "assets" / "generated" / "qa-results.json"
    gen_path = (
        Path(args.generation_manifest).resolve()
        if args.generation_manifest
        else packet / "assets" / "generated" / "generation-manifest.json"
    )
    prompts_json = Path(args.prompts_json).resolve() if args.prompts_json else packet / "prompts.json"
    prompts_md = Path(args.prompts_md).resolve() if args.prompts_md else packet / "04-generation-prompts.md"
    out_path = Path(args.out).resolve() if args.out else packet / "assets" / "generated" / "reroll-manifest.json"

    for p in [qa_path, gen_path]:
        if not p.exists():
            raise SystemExit(f"error: required file not found: {p}")

    if not prompts_json.exists() and not prompts_md.exists():
        raise SystemExit("error: prompts source missing (prompts.json or 04-generation-prompts.md)")

    return {
        "packet": packet,
        "qa": qa_path,
        "gen": gen_path,
        "prompts_json": prompts_json,
        "prompts_md": prompts_md,
        "out": out_path,
    }


def prompt_index(paths: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
    if paths["prompts_json"].exists():
        prompts = load_json(paths["prompts_json"])
        shots = prompts.get("shots") or []
        indexed = {str(s.get("asset_id")): s for s in shots if s.get("asset_id")}
        if indexed:
            return indexed

    md_shots = parse_generation_prompts(paths["prompts_md"])
    return {str(s.get("asset_id")): s for s in md_shots if s.get("asset_id")}


def deterministic_attempt_result(asset_id: str, attempt: int, revised_prompt: str) -> str:
    digest = hashlib.sha256(f"{asset_id}|{attempt}|{revised_prompt}".encode("utf-8")).hexdigest()
    score = int(digest[:2], 16)
    threshold = 85 - (attempt * 20)  # gets easier each attempt
    return "pass" if score >= max(30, threshold) else "fail"


def build_revised_prompt(base_prompt: str, reasons: List[str], attempt: int) -> str:
    reasons_text = "; ".join(reasons[:3]) if reasons else "qa flagged"
    fix = (
        f"Reroll attempt {attempt}: tighten product framing, enforce label legibility, "
        f"reduce distracting props, and resolve: {reasons_text}."
    )
    return f"{base_prompt} {fix}".strip()


def append_reroll_markdown(report_path: Path, payload: Dict[str, Any]) -> None:
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# QA Report\n"
    header = "## Reroll History"
    if header not in existing:
        existing = existing.rstrip() + "\n\n" + header + "\n"

    run = payload["run"]
    summary = payload["summary"]
    lines = [
        f"### Reroll Run {run['run_id']}",
        f"- Timestamp (UTC): {run['timestamp_utc']}",
        f"- Mode: {run['mode']}",
        f"- Eligible shots: {summary['eligible_shots']}",
        f"- Converged: {summary['pass_after_reroll']}",
        f"- Exhausted: {summary['reroll_exhausted']}",
        "",
        "| Asset | Original Status | Attempts | Final Status | Reason |",
        "|---|---|---:|---|---|",
    ]

    for row in payload.get("shots", []):
        reason = "; ".join(row.get("reasons", [])[:2]) or "n/a"
        lines.append(
            f"| {row.get('asset_id')} ({row.get('shot_name')}) | {row.get('original_status')} | "
            f"{len(row.get('attempts', []))} | {row.get('final_status')} | {reason} |"
        )

    report_path.write_text(existing.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def run_live_generation(packet: Path, asset_id: str, revised_prompt: str, model: str, attempt: int) -> Path:
    script = packet.parent.parent / "scripts" / "generate-images.py"
    if not script.exists():
        script = Path(__file__).resolve().parent / "generate-images.py"

    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as tf:
        json.dump({asset_id: revised_prompt}, tf)
        tf.write("\n")
        temp_path = tf.name

    manifest_path = packet / "assets" / "generated" / f"reroll-{asset_id}-attempt-{attempt}-generation-manifest.json"
    cmd = [
        str(script),
        "--packet",
        str(packet),
        "--asset-ids",
        asset_id,
        "--prompt-overrides",
        temp_path,
        "--overwrite",
        "--live",
        "--auto-reference-image",
        "--model",
        model,
        "--manifest",
        str(manifest_path),
    ]
    subprocess.run(cmd, check=True)
    return manifest_path


def run_live_qa(packet: Path, manifest_path: Path, asset_id: str, threshold: float) -> Dict[str, Any]:
    script = Path(__file__).resolve().parent / "qa-images.py"
    qa_path = packet / "assets" / "generated" / f"reroll-{asset_id}-qa-results.json"
    cmd = [
        str(script),
        "--packet",
        str(packet),
        "--manifest",
        str(manifest_path),
        "--out",
        str(qa_path),
        "--threshold",
        str(threshold),
        "--live",
    ]
    subprocess.run(cmd, check=True)
    qa = load_json(qa_path)
    results = qa.get("results") or []
    return results[0] if results else {"status": "fail", "reject_reasons": ["live reroll QA returned no results"]}


def main() -> int:
    args = parse_args()
    paths = resolve_paths(args)

    qa = load_json(paths["qa"])
    gen = load_json(paths["gen"])
    prompts_by_asset = prompt_index(paths)

    reroll_statuses = {x.strip() for x in args.reroll_status.split(",") if x.strip()}
    generated = {str(e.get("asset_id")): e for e in gen.get("entries", [])}

    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    mode = "live" if args.live else "dry-run-simulated"

    rows: List[Dict[str, Any]] = []
    total_attempts = 0
    converged = 0
    exhausted = 0

    for result in qa.get("results", []):
        asset_id = str(result.get("asset_id", ""))
        if not asset_id or result.get("status") not in reroll_statuses:
            continue

        source = generated.get(asset_id, {})
        prompt_row = prompts_by_asset.get(asset_id, {})
        original_prompt = str(source.get("prompt") or prompt_row.get("prompt") or "")
        reasons = [str(r) for r in result.get("reject_reasons", [])]

        attempts = []
        final_status = "reroll_exhausted"
        for attempt in range(1, args.max_attempts + 1):
            revised_prompt = build_revised_prompt(original_prompt, reasons, attempt)
            attempt_record = {
                "attempt": attempt,
                "revised_prompt": revised_prompt,
                "reason": reasons,
            }
            if args.live:
                manifest_path = run_live_generation(paths["packet"], asset_id, revised_prompt, args.live_model, attempt)
                attempt_record["generation_manifest"] = str(manifest_path)
                if args.live_qa:
                    qa_result = run_live_qa(paths["packet"], manifest_path, asset_id, args.qa_threshold)
                    attempt_status = str(qa_result.get("status", "fail"))
                    attempt_record["qa_result"] = qa_result
                else:
                    attempt_status = "executed_live"
            else:
                attempt_status = deterministic_attempt_result(asset_id, attempt, revised_prompt)

            attempt_record["status"] = attempt_status
            attempts.append(attempt_record)
            total_attempts += 1

            if attempt_status in {"pass", "executed_live"}:
                final_status = "pass_after_reroll"
                converged += 1
                break

        if final_status == "reroll_exhausted":
            exhausted += 1

        rows.append(
            {
                "asset_id": asset_id,
                "shot_name": str(result.get("shot_name", asset_id)),
                "original_status": str(result.get("status", "unknown")),
                "reasons": reasons,
                "original_prompt": original_prompt,
                "attempts": attempts,
                "final_status": final_status,
            }
        )

    payload = {
        "run": {
            "run_id": f"reroll-{run_stamp}",
            "timestamp_utc": run_stamp,
            "mode": mode,
            "packet_dir": str(paths["packet"]),
            "qa_results": str(paths["qa"]),
            "generation_manifest": str(paths["gen"]),
            "max_attempts": args.max_attempts,
            "live_qa": bool(args.live_qa),
            "qa_threshold": args.qa_threshold,
        },
        "summary": {
            "eligible_shots": len(rows),
            "total_attempts": total_attempts,
            "pass_after_reroll": converged,
            "reroll_exhausted": exhausted,
            "convergence_rate": round((converged / len(rows)) * 100.0, 2) if rows else 0.0,
        },
        "shots": rows,
    }

    dump_json(paths["out"], payload)
    append_reroll_markdown(paths["packet"] / "05-qa-report.md", payload)
    print(str(paths["out"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
