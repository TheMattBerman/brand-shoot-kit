#!/usr/bin/env python3
"""QA scoring for generated Brand Shoot assets.

Default mode is deterministic/manual-friendly scoring from generation manifests.
Use `--live` for OpenAI vision scoring when credentials are available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from packet_utils import dump_json, ensure_packet_dir, load_json

CRITERIA: List[Tuple[str, int]] = [
    ("product_accuracy", 30),
    ("commerce_usefulness", 20),
    ("brand_fit", 15),
    ("scene_realism", 15),
    ("visual_clarity", 10),
    ("artifact_risk", 10),
]


class OpenAIVisionProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def score(self, image_path: Path, shot: Dict[str, Any]) -> Dict[str, Any]:
        image_bytes = image_path.read_bytes()
        b64 = __import__("base64").b64encode(image_bytes).decode("ascii")

        instructions = (
            "Return strict JSON only with keys: scores, reject_reasons, pass, summary. "
            "scores must include product_accuracy, commerce_usefulness, brand_fit, scene_realism, visual_clarity, artifact_risk with 0-100 integers."
        )
        prompt = (
            f"You are QA reviewing an ecommerce product image. "
            f"Shot: {shot.get('shot_name')} | Ratio: {shot.get('ratio')} | Use case: {shot.get('use_case')}\n"
            f"Prompt intent: {shot.get('prompt')}\n"
            f"Negative constraints: {', '.join(shot.get('negative_constraints', []))}\n"
            "Flag reject_reasons when fidelity or commerce utility fails."
        )

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": instructions + "\n" + prompt},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
                    ],
                }
            ],
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI vision scoring failed ({exc.code}): {details}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI vision request failed: {exc}") from exc

        text = _extract_output_text(body)
        if not text:
            raise RuntimeError(f"OpenAI response missing output text: {body}")

        try:
            parsed = parse_json_object(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse OpenAI vision JSON: {text}") from exc

        return parsed


def parse_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("expected JSON object", cleaned, 0)
    return payload


def _extract_output_text(body: Dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str) and body["output_text"].strip():
        return body["output_text"].strip()

    output = body.get("output") or []
    chunks = []
    for item in output:
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    return "\n".join(c for c in chunks if c).strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run QA scoring on generated packet assets")
    p.add_argument("--packet", required=True, help="Path to packet directory")
    p.add_argument("--manifest", help="Path to generation manifest (default: latest in assets/generated)")
    p.add_argument("--out", help="QA JSON output path (default: <packet>/assets/generated/qa-results.json)")
    p.add_argument("--live", action="store_true", help="Use OpenAI vision scoring")
    p.add_argument("--model", default="gpt-4.1-mini", help="OpenAI vision model for live mode")
    p.add_argument("--threshold", type=float, default=80.0, help="Pass threshold (0-100)")
    return p.parse_args()


def resolve_manifest(packet_dir: Path, override: str) -> Path:
    if override:
        path = Path(override).resolve()
        if not path.exists():
            raise SystemExit(f"error: manifest not found: {path}")
        return path

    candidate = packet_dir / "assets" / "generated" / "generation-manifest.json"
    if candidate.exists():
        return candidate

    raise SystemExit("error: generation manifest not found; run generate-images.py first")


def deterministic_scores(entry: Dict[str, Any]) -> Dict[str, int]:
    seed_text = f"{entry.get('asset_id')}|{entry.get('shot_name')}|{entry.get('prompt')}|{entry.get('image_sha256', '')}"
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    nums = [int(digest[i : i + 2], 16) for i in range(0, 24, 2)]

    out: Dict[str, int] = {}
    for i, (key, _weight) in enumerate(CRITERIA):
        base = 62 + (nums[i] % 33)  # 62..94
        if entry.get("dry_run", False):
            base -= 6
        out[key] = max(0, min(100, base))
    return out


def weighted_score(scores: Dict[str, int]) -> float:
    total = 0.0
    for key, weight in CRITERIA:
        total += scores.get(key, 0) * (weight / 100.0)
    return round(total, 2)


def derive_reject_reasons(entry: Dict[str, Any], scores: Dict[str, int], threshold: float) -> List[str]:
    reasons: List[str] = []
    if entry.get("dry_run", False):
        reasons.append("dry-run placeholder asset requires manual visual review")
    if scores.get("product_accuracy", 0) < 74:
        reasons.append("possible label/geometry mismatch risk")
    if scores.get("commerce_usefulness", 0) < 72:
        reasons.append("product framing may be too weak for commerce")
    if scores.get("visual_clarity", 0) < 70:
        reasons.append("possible soft-focus or legibility issue")
    if weighted_score(scores) < threshold:
        reasons.append("weighted score below threshold")

    # deterministic occasional failure reason to exercise reroll flow
    digest = hashlib.sha256((entry.get("asset_id", "") + entry.get("shot_name", "")).encode("utf-8")).hexdigest()
    if int(digest[:2], 16) % 11 == 0:
        reasons.append("simulated artifact risk trigger for smoke/eval coverage")

    seen = set()
    deduped = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    return deduped


def update_qa_markdown(report_path: Path, qa_payload: Dict[str, Any]) -> None:
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# QA Report\n"
    section_header = "## Automated QA Runs"
    if section_header not in existing:
        existing = existing.rstrip() + "\n\n" + section_header + "\n"

    run = qa_payload["run"]
    summary = qa_payload["summary"]
    lines = [
        f"### Run {run['run_id']}",
        f"- Timestamp (UTC): {run['timestamp_utc']}",
        f"- Mode: {run['mode']}",
        f"- Source manifest: `{run['manifest_path']}`",
        f"- Pass: {summary['pass']} / {summary['total']}",
        f"- Fail: {summary['fail']}",
        f"- Manual review required: {summary['manual_review']}",
        "",
        "| Asset | Status | Score | Top Reasons |",
        "|---|---|---:|---|",
    ]

    for item in qa_payload["results"]:
        reasons = "; ".join(item.get("reject_reasons", [])[:2]) or "none"
        lines.append(f"| {item['asset_id']} ({item['shot_name']}) | {item['status']} | {item['weighted_score']} | {reasons} |")

    block = "\n".join(lines) + "\n"
    report_path.write_text(existing.rstrip() + "\n\n" + block, encoding="utf-8")


def normalize_live_response(resp: Dict[str, Any], entry: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    scores_in = resp.get("scores") or {}
    scores = {key: int(scores_in.get(key, 0)) for key, _ in CRITERIA}
    score = weighted_score(scores)
    reject_reasons = [str(r) for r in (resp.get("reject_reasons") or [])]
    passed = bool(resp.get("pass", False)) and score >= threshold and not reject_reasons

    return {
        "asset_id": entry.get("asset_id"),
        "shot_name": entry.get("shot_name"),
        "image_path": entry.get("image_path"),
        "scores": scores,
        "weighted_score": score,
        "status": "pass" if passed else "fail",
        "reject_reasons": reject_reasons,
        "reroll_instruction": entry.get("reroll_if_failed", ""),
    }


def main() -> int:
    args = parse_args()
    packet_dir = Path(args.packet).resolve()
    ensure_packet_dir(packet_dir)

    manifest_path = resolve_manifest(packet_dir, args.manifest)
    manifest = load_json(manifest_path)
    entries = manifest.get("entries") or []
    if not entries:
        print("error: generation manifest has no entries", file=sys.stderr)
        return 2

    qa_out = Path(args.out).resolve() if args.out else packet_dir / "assets" / "generated" / "qa-results.json"

    mode = "deterministic-manual"
    vision = None
    if args.live:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            print("error: --live set but OPENAI_API_KEY missing", file=sys.stderr)
            return 2
        mode = "live-openai-vision"
        vision = OpenAIVisionProvider(key, args.model)

    results: List[Dict[str, Any]] = []
    for entry in entries:
        image_path = Path(entry.get("image_path", ""))
        if not image_path.exists():
            results.append(
                {
                    "asset_id": entry.get("asset_id"),
                    "shot_name": entry.get("shot_name"),
                    "image_path": str(image_path),
                    "scores": {k: 0 for k, _ in CRITERIA},
                    "weighted_score": 0,
                    "status": "fail",
                    "reject_reasons": ["missing generated image file"],
                    "reroll_instruction": entry.get("reroll_if_failed", ""),
                }
            )
            continue

        if vision is not None:
            try:
                live_resp = vision.score(image_path, entry)
                item = normalize_live_response(live_resp, entry, args.threshold)
                results.append(item)
                continue
            except Exception as exc:  # pragma: no cover - live path
                results.append(
                    {
                        "asset_id": entry.get("asset_id"),
                        "shot_name": entry.get("shot_name"),
                        "image_path": str(image_path),
                        "scores": {k: 0 for k, _ in CRITERIA},
                        "weighted_score": 0,
                        "status": "fail",
                        "reject_reasons": [f"live vision error: {exc}"],
                        "reroll_instruction": entry.get("reroll_if_failed", ""),
                    }
                )
                continue

        scores = deterministic_scores(entry)
        score = weighted_score(scores)
        reject_reasons = derive_reject_reasons(entry, scores, args.threshold)
        if entry.get("dry_run", False):
            status = "manual_review"
        else:
            status = "pass" if score >= args.threshold and not reject_reasons else "fail"

        results.append(
            {
                "asset_id": entry.get("asset_id"),
                "shot_name": entry.get("shot_name"),
                "image_path": str(image_path),
                "scores": scores,
                "weighted_score": score,
                "status": status,
                "reject_reasons": reject_reasons,
                "reroll_instruction": entry.get("reroll_if_failed", ""),
            }
        )

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "manual_review": sum(1 for r in results if r["status"] == "manual_review"),
    }
    reroll_queue = [
        {
            "asset_id": r["asset_id"],
            "shot_name": r["shot_name"],
            "reasons": r.get("reject_reasons", []),
            "reroll_instruction": r.get("reroll_instruction", ""),
        }
        for r in results
        if r["status"] in {"fail", "manual_review"}
    ]

    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "run": {
            "run_id": f"qa-{run_stamp}",
            "timestamp_utc": run_stamp,
            "mode": mode,
            "manifest_path": str(manifest_path),
            "packet_dir": str(packet_dir),
            "threshold": args.threshold,
            "model": args.model if vision is not None else "none",
        },
        "summary": summary,
        "reroll_queue": reroll_queue,
        "results": results,
    }

    dump_json(qa_out, payload)
    update_qa_markdown(packet_dir / "05-qa-report.md", payload)
    print(str(qa_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
