#!/usr/bin/env python3
"""Build human-review artifacts for a packet.

Outputs:
- human-review-template.json
- contact-sheet.html
- artifact-pack-manifest.json
"""

from __future__ import annotations

import argparse
import html
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from packet_utils import dump_json, ensure_packet_dir, load_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Package review artifacts from packet manifests")
    p.add_argument("--packet", required=True, help="Packet directory")
    p.add_argument("--generation-manifest", help="Generation manifest path")
    p.add_argument("--qa-results", help="QA results path")
    p.add_argument("--reroll-manifest", help="Reroll manifest path")
    p.add_argument("--export-manifest", help="Export manifest path")
    p.add_argument("--out", help="Output review directory (default: <packet>/assets/review)")
    return p.parse_args()


def resolve_path(packet: Path, override: Optional[str], default_rel: Path) -> Path:
    if override:
        path = Path(override).resolve()
    else:
        path = packet / default_rel
    if not path.exists():
        raise SystemExit(f"error: required input not found: {path}")
    return path


def resolve_export_manifest(packet: Path, override: Optional[str]) -> Path:
    if override:
        path = Path(override).resolve()
        if not path.exists():
            raise SystemExit(f"error: export manifest not found: {path}")
        return path
    found = sorted(packet.glob("assets/exports/**/export-manifest.json"))
    if not found:
        raise SystemExit("error: export manifest not found under packet assets/exports")
    return found[-1]


def qa_index(qa: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in qa.get("results", []):
        out[str(row.get("asset_id", ""))] = row
    return out


def reroll_index(reroll: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in reroll.get("shots", []):
        out[str(row.get("asset_id", ""))] = row
    return out


def export_index(export_manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in export_manifest.get("records", []):
        out[str(row.get("asset_id", ""))] = row
    return out


def decision_for(
    *,
    qa_status: str,
    reroll_final_status: str,
    image_exists: bool,
) -> Tuple[str, str]:
    if not image_exists:
        return "reject", "source image missing"
    if reroll_final_status == "reroll_exhausted":
        return "reject", "reroll exhausted"
    if qa_status == "pass" or reroll_final_status == "pass_after_reroll":
        return "approve", "qa pass or pass after reroll"
    if qa_status in {"fail", "manual_review"}:
        return "reroll", f"qa status is {qa_status}"
    return "reroll", "insufficient qa confidence"


def relpath(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path.resolve())


def html_row(row: Dict[str, Any]) -> str:
    reasons = row.get("reject_reasons") or []
    outputs = row.get("export_outputs") or []
    reasons_text = "<br/>".join(html.escape(str(x)) for x in reasons[:3]) or "none"
    channels_text = "<br/>".join(html.escape(str(x.get("channel", ""))) for x in outputs) or "none"
    img_src = html.escape(str(row.get("image_path_for_html", "")))
    return (
        "<tr>"
        f"<td>{html.escape(str(row.get('asset_id', '')))}</td>"
        f"<td>{html.escape(str(row.get('shot_name', '')))}</td>"
        f"<td>{html.escape(str(row.get('suggested_decision', '')))}</td>"
        f"<td>{html.escape(str(row.get('qa_status', '')))}</td>"
        f"<td>{html.escape(str(row.get('weighted_score', '')))}</td>"
        f"<td>{reasons_text}</td>"
        f"<td>{channels_text}</td>"
        f"<td><img src=\"{img_src}\" alt=\"{html.escape(str(row.get('asset_id', '')))}\"/></td>"
        "</tr>"
    )


def build_contact_sheet_html(
    *,
    packet: Path,
    out_dir: Path,
    rows: List[Dict[str, Any]],
    reference_image: Optional[Path],
    export_manifest_path: Path,
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    ref_html = "<p>Reference image: none</p>"
    if reference_image and reference_image.exists():
        src = html.escape(relpath(reference_image, out_dir))
        ref_html = (
            "<div class=\"ref\">"
            "<h2>Reference Image</h2>"
            f"<img src=\"{src}\" alt=\"reference image\"/>"
            "</div>"
        )
    table_rows = "\n".join(html_row(row) for row in rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Brand Shoot Contact Sheet</title>
  <style>
    :root {{
      --bg: #f4f3ef;
      --ink: #181818;
      --muted: #6b6b6b;
      --line: #d9d4c8;
      --accent: #935f2d;
    }}
    body {{ background: var(--bg); color: var(--ink); font-family: "IBM Plex Sans", "Helvetica Neue", sans-serif; margin: 24px; }}
    h1, h2 {{ margin: 0 0 12px 0; }}
    p {{ color: var(--muted); margin: 0 0 10px 0; }}
    .meta {{ margin-bottom: 16px; }}
    .ref img {{ width: min(360px, 90vw); border: 1px solid var(--line); background: #fff; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 18px; background: #fff; }}
    th, td {{ border: 1px solid var(--line); padding: 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #f2ede3; text-align: left; }}
    td img {{ width: 132px; height: 132px; object-fit: contain; background: #fff; border: 1px solid var(--line); }}
    .decision-approve {{ color: #1e6e3e; font-weight: 700; }}
    .decision-reroll {{ color: #8b5b00; font-weight: 700; }}
    .decision-reject {{ color: #9e1f1f; font-weight: 700; }}
    .foot {{ margin-top: 14px; font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <h1>Brand Shoot Contact Sheet</h1>
  <div class="meta">
    <p>Generated: {html.escape(timestamp)}</p>
    <p>Packet: {html.escape(str(packet))}</p>
    <p>Export manifest: {html.escape(str(export_manifest_path))}</p>
  </div>
  {ref_html}
  <h2>Generated Assets</h2>
  <table>
    <thead>
      <tr>
        <th>Asset</th>
        <th>Shot</th>
        <th>Suggested Decision</th>
        <th>QA</th>
        <th>Score</th>
        <th>Top Reasons</th>
        <th>Export Channels</th>
        <th>Preview</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
  <p class="foot">Decisions are suggestions only; final approve/reroll/reject is human-owned.</p>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    packet = Path(args.packet).resolve()
    ensure_packet_dir(packet)

    generation_path = resolve_path(packet, args.generation_manifest, Path("assets/generated/generation-manifest.json"))
    qa_path = resolve_path(packet, args.qa_results, Path("assets/generated/qa-results.json"))
    reroll_path = Path(args.reroll_manifest).resolve() if args.reroll_manifest else packet / "assets/generated/reroll-manifest.json"
    export_path = resolve_export_manifest(packet, args.export_manifest)
    out_dir = Path(args.out).resolve() if args.out else packet / "assets" / "review"
    out_dir.mkdir(parents=True, exist_ok=True)

    generation = load_json(generation_path)
    qa = load_json(qa_path)
    reroll = load_json(reroll_path) if reroll_path.exists() else {"shots": [], "summary": {}}
    export_manifest = load_json(export_path)

    qa_by_asset = qa_index(qa)
    reroll_by_asset = reroll_index(reroll)
    export_by_asset = export_index(export_manifest)

    rows: List[Dict[str, Any]] = []
    decision_counts = {"approve": 0, "reroll": 0, "reject": 0}
    qa_counts: Dict[str, int] = {}

    for entry in generation.get("entries", []):
        asset_id = str(entry.get("asset_id", ""))
        shot_name = str(entry.get("shot_name", asset_id))
        image_path = Path(str(entry.get("image_path", "")))
        qa_row = qa_by_asset.get(asset_id, {})
        reroll_row = reroll_by_asset.get(asset_id, {})
        export_row = export_by_asset.get(asset_id, {})

        qa_status = str(qa_row.get("status", "unscored"))
        reroll_status = str(reroll_row.get("final_status", "not_run"))
        decision, reason = decision_for(
            qa_status=qa_status,
            reroll_final_status=reroll_status,
            image_exists=image_path.exists(),
        )
        decision_counts[decision] += 1
        qa_counts[qa_status] = qa_counts.get(qa_status, 0) + 1

        image_for_html = relpath(image_path, out_dir) if image_path.exists() else ""
        rows.append(
            {
                "asset_id": asset_id,
                "shot_name": shot_name,
                "image_path": str(image_path),
                "image_path_for_html": image_for_html,
                "qa_status": qa_status,
                "weighted_score": qa_row.get("weighted_score"),
                "reject_reasons": qa_row.get("reject_reasons") or [],
                "reroll_final_status": reroll_status,
                "suggested_decision": decision,
                "decision_reason": reason,
                "export_outputs": export_row.get("outputs") or [],
            }
        )

    reference_image_path = generation.get("reference_image_path")
    reference_image = Path(str(reference_image_path)).resolve() if reference_image_path else None
    if reference_image and not reference_image.exists():
        reference_image = None

    template_path = out_dir / "human-review-template.json"
    html_path = out_dir / "contact-sheet.html"
    manifest_path = out_dir / "artifact-pack-manifest.json"

    template = {
        "review_meta": {
            "review_date": "YYYY-MM-DD",
            "reviewer": "Name",
            "packet_dir": str(packet),
            "product_url": str(load_json(packet / "scout.json").get("url", "")),
            "run_mode": str(generation.get("provider", "unknown")),
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "decision_summary": {
            "suggested_approve": decision_counts["approve"],
            "suggested_reroll": decision_counts["reroll"],
            "suggested_reject": decision_counts["reject"],
        },
        "human_judgment": {
            "product_accuracy": "pass|mixed|fail",
            "label_fidelity": "pass|mixed|fail",
            "realism": "pass|mixed|fail",
            "commerce_usefulness": "pass|mixed|fail",
        },
        "asset_reviews": [
            {
                "asset_id": row["asset_id"],
                "shot_name": row["shot_name"],
                "suggested_decision": row["suggested_decision"],
                "suggested_reason": row["decision_reason"],
                "qa_status": row["qa_status"],
                "decision": "approve|reroll|reject",
                "reasons": [],
                "reroll_direction": "",
            }
            for row in rows
        ],
        "qa_calibration": {
            "qa_threshold_before": qa.get("run", {}).get("threshold", 80),
            "qa_threshold_after": qa.get("run", {}).get("threshold", 80),
            "threshold_change_reason": "none",
            "rubric_tweaks": [],
        },
        "go_no_go": {
            "expand_to_12_shots": False,
            "decision_reason": "Fill after review",
        },
    }
    dump_json(template_path, template)

    html_payload = build_contact_sheet_html(
        packet=packet,
        out_dir=out_dir,
        rows=rows,
        reference_image=reference_image,
        export_manifest_path=export_path,
    )
    html_path.write_text(html_payload, encoding="utf-8")

    manifest = {
        "run": {
            "run_id": f"review-pack-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
            "timestamp_utc": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
            "packet_dir": str(packet),
            "generation_manifest": str(generation_path),
            "qa_results": str(qa_path),
            "reroll_manifest": str(reroll_path) if reroll_path.exists() else None,
            "export_manifest": str(export_path),
            "reference_image_path": str(reference_image) if reference_image else None,
            "out_dir": str(out_dir),
        },
        "summary": {
            "total_assets": len(rows),
            "qa_status_counts": qa_counts,
            "suggested_decisions": decision_counts,
            "packaged_for_review": len(rows),
        },
        "artifacts": {
            "human_review_template": str(template_path),
            "contact_sheet_html": str(html_path),
        },
    }
    dump_json(manifest_path, manifest)
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

