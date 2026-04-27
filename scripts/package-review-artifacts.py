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


def ratio_from_dimensions(dimensions: List[int]) -> str:
    if len(dimensions) != 2:
        return "unknown"
    width, height = dimensions
    known = {
        (1, 1): "1:1",
        (4, 5): "4:5",
        (9, 16): "9:16",
        (16, 9): "16:9",
    }
    for (a, b), label in known.items():
        if width * b == height * a:
            return label
    return f"{width}:{height}"


def row_card(row: Dict[str, Any]) -> str:
    reasons = row.get("reject_reasons") or []
    outputs = row.get("export_outputs") or []
    score = row.get("weighted_score")
    score_text = "n/a" if score is None else str(score)
    qa_status = str(row.get("qa_status", "unscored"))
    decision = str(row.get("suggested_decision", "reroll"))
    entry_dims = row.get("entry_dimensions") or []
    entry_ratio = ratio_from_dimensions(entry_dims) if entry_dims else "unknown"
    channels = ", ".join(str(x.get("channel", "")) for x in outputs if x.get("channel")) or "none"

    top_output = outputs[0] if outputs else {}
    out_dims = top_output.get("output_dimensions") or []
    out_ratio = ratio_from_dimensions(out_dims) if out_dims else "unknown"
    render_mode = str(top_output.get("render_mode", "unknown"))

    reasons_html = "".join(f"<li>{html.escape(str(x))}</li>" for x in reasons[:4]) or "<li>none</li>"
    img_src = html.escape(str(row.get("image_path_for_html", "")))

    scores = row.get("scores") or {}
    qa_breakdown = " ".join(
        [
            f"PA {scores.get('product_accuracy', '-')}",
            f"CU {scores.get('commerce_usefulness', '-')}",
            f"BF {scores.get('brand_fit', '-')}",
            f"SR {scores.get('scene_realism', '-')}",
            f"VC {scores.get('visual_clarity', '-')}",
            f"AR {scores.get('artifact_risk', '-')}",
        ]
    )

    return (
        f"<article class=\"card decision-{html.escape(decision)} qa-{html.escape(qa_status)}\" "
        f"data-decision=\"{html.escape(decision)}\" data-qa=\"{html.escape(qa_status)}\" data-channels=\"{html.escape(channels.lower())}\" "
        f"data-name=\"{html.escape(str(row.get('shot_name', '')).lower())}\">"
        "<div class=\"card-head\">"
        f"<h3>{html.escape(str(row.get('asset_id', '')))} - {html.escape(str(row.get('shot_name', '')))}</h3>"
        "<div class=\"badges\">"
        f"<span class=\"pill decision\">{html.escape(decision)}</span>"
        f"<span class=\"pill qa\">{html.escape(qa_status)}</span>"
        f"<span class=\"pill score\">score {html.escape(score_text)}</span>"
        "</div></div>"
        "<div class=\"media\">"
        f"<img src=\"{img_src}\" alt=\"{html.escape(str(row.get('asset_id', '')))}\"/>"
        "</div>"
        "<dl class=\"meta\">"
        f"<div><dt>Decision reason</dt><dd>{html.escape(str(row.get('decision_reason', '')))}</dd></div>"
        f"<div><dt>Channels</dt><dd>{html.escape(channels)}</dd></div>"
        f"<div><dt>Source dims/ratio</dt><dd>{html.escape(' x '.join(str(v) for v in entry_dims) if entry_dims else 'unknown')} ({html.escape(entry_ratio)})</dd></div>"
        f"<div><dt>Output dims/ratio</dt><dd>{html.escape(' x '.join(str(v) for v in out_dims) if out_dims else 'unknown')} ({html.escape(out_ratio)})</dd></div>"
        f"<div><dt>Render mode</dt><dd>{html.escape(render_mode)}</dd></div>"
        f"<div><dt>QA breakdown</dt><dd>{html.escape(qa_breakdown)}</dd></div>"
        "</dl>"
        "<div class=\"reasons\"><strong>Top reasons</strong><ul>"
        f"{reasons_html}"
        "</ul></div>"
        "</article>"
    )


def build_contact_sheet_html(
    *,
    packet: Path,
    out_dir: Path,
    rows: List[Dict[str, Any]],
    reference_image: Optional[Path],
    reference_image_url: Optional[str],
    export_manifest_path: Path,
    decision_counts: Dict[str, int],
    qa_counts: Dict[str, int],
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    ref_html = "<p>Reference image: none</p>"
    if reference_image and reference_image.exists():
        src = html.escape(relpath(reference_image, out_dir))
        ref_html = (
            "<div class=\"ref\">"
            "<h2>Reference</h2>"
            f"<img src=\"{src}\" alt=\"reference image\"/>"
            f"<p>Local: {html.escape(str(reference_image))}</p>"
            f"<p>URL: {html.escape(reference_image_url or 'none')}</p>"
            "</div>"
        )

    cards = "\n".join(row_card(row) for row in rows)

    qa_summary = ", ".join(f"{k} {v}" for k, v in sorted(qa_counts.items())) or "none"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Brand Shoot Review Dashboard</title>
  <style>
    :root {{
      --bg: #f2eee7;
      --panel: #fffdf9;
      --ink: #1d1a17;
      --muted: #6f665c;
      --line: #d9cec0;
      --ok: #1f7a47;
      --warn: #8d5d00;
      --bad: #9d1f1f;
      --accent: #5b3d1d;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: radial-gradient(circle at 20% 10%, #f7f4ee, var(--bg)); color: var(--ink); font-family: "IBM Plex Sans", "Avenir Next", sans-serif; }}
    .wrap {{ max-width: 1320px; margin: 0 auto; padding: 20px; }}
    h1, h2, h3 {{ margin: 0; }}
    .top {{ display: grid; gap: 12px; grid-template-columns: 2fr 1fr; align-items: start; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; }}
    .meta p {{ margin: 0 0 6px 0; color: var(--muted); font-size: 13px; }}
    .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }}
    .kpi {{ border: 1px solid var(--line); border-radius: 10px; padding: 8px; background: #fff; }}
    .kpi .label {{ color: var(--muted); font-size: 12px; }}
    .kpi .value {{ font-size: 20px; font-weight: 700; }}
    .kpi.approve .value {{ color: var(--ok); }}
    .kpi.reroll .value {{ color: var(--warn); }}
    .kpi.reject .value {{ color: var(--bad); }}
    .ref img {{ width: 100%; max-width: 360px; border: 1px solid var(--line); border-radius: 10px; background: #fff; }}
    .controls {{ margin-top: 14px; display: grid; gap: 8px; grid-template-columns: 1fr 1fr 1fr 2fr; }}
    .controls select, .controls input {{ width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px; font-size: 13px; }}
    .cards {{ margin-top: 14px; display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); }}
    .card {{ border: 1px solid var(--line); border-radius: 12px; background: var(--panel); padding: 10px; box-shadow: 0 2px 0 rgba(0,0,0,0.02); }}
    .card-head {{ display: flex; justify-content: space-between; gap: 8px; align-items: start; }}
    .card-head h3 {{ font-size: 15px; line-height: 1.2; }}
    .badges {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: end; }}
    .pill {{ display: inline-flex; border-radius: 999px; border: 1px solid var(--line); padding: 2px 8px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .decision-approve .pill.decision {{ background: #e8f6ee; border-color: #bee6ce; color: var(--ok); }}
    .decision-reroll .pill.decision {{ background: #fff4de; border-color: #efd69b; color: var(--warn); }}
    .decision-reject .pill.decision {{ background: #fde8e8; border-color: #f2baba; color: var(--bad); }}
    .media {{ margin-top: 8px; }}
    .media img {{ width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: #fff; border: 1px solid var(--line); border-radius: 10px; }}
    .meta {{ margin-top: 8px; display: grid; gap: 4px; }}
    .meta div {{ display: grid; grid-template-columns: 140px 1fr; gap: 8px; font-size: 12px; }}
    .meta dt {{ color: var(--muted); }}
    .meta dd {{ margin: 0; }}
    .reasons {{ margin-top: 8px; font-size: 12px; }}
    .reasons ul {{ margin: 6px 0 0 16px; padding: 0; }}
    .hidden {{ display: none !important; }}
    @media (max-width: 1020px) {{
      .top {{ grid-template-columns: 1fr; }}
      .controls {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 640px) {{
      .controls {{ grid-template-columns: 1fr; }}
      .cards {{ grid-template-columns: 1fr; }}
      .meta div {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <section class="panel meta">
        <h1>Brand Shoot Review Dashboard</h1>
        <p>Generated: {html.escape(timestamp)}</p>
        <p>Packet: {html.escape(str(packet))}</p>
        <p>Export manifest: {html.escape(str(export_manifest_path))}</p>
        <p>QA status mix: {html.escape(qa_summary)}</p>
        <div class="summary">
          <div class="kpi approve"><div class="label">Suggest approve</div><div class="value">{decision_counts.get('approve', 0)}</div></div>
          <div class="kpi reroll"><div class="label">Suggest reroll</div><div class="value">{decision_counts.get('reroll', 0)}</div></div>
          <div class="kpi reject"><div class="label">Suggest reject</div><div class="value">{decision_counts.get('reject', 0)}</div></div>
        </div>
      </section>
      <section class="panel">
        {ref_html}
      </section>
    </div>

    <section class="panel controls">
      <select id="filter-decision">
        <option value="">All decisions</option>
        <option value="approve">Approve</option>
        <option value="reroll">Reroll</option>
        <option value="reject">Reject</option>
      </select>
      <select id="filter-qa">
        <option value="">All QA</option>
        <option value="pass">pass</option>
        <option value="manual_review">manual_review</option>
        <option value="fail">fail</option>
        <option value="unscored">unscored</option>
      </select>
      <input id="filter-channel" type="text" placeholder="Filter channel (instagram, pdp, amazon...)" />
      <input id="filter-name" type="text" placeholder="Filter by shot name or asset id" />
    </section>

    <section id="cards" class="cards">
      {cards}
    </section>
  </div>

  <script>
    (function () {{
      const cards = Array.from(document.querySelectorAll('.card'));
      const decision = document.getElementById('filter-decision');
      const qa = document.getElementById('filter-qa');
      const channel = document.getElementById('filter-channel');
      const name = document.getElementById('filter-name');

      function applyFilters() {{
        const d = (decision.value || '').toLowerCase().trim();
        const q = (qa.value || '').toLowerCase().trim();
        const c = (channel.value || '').toLowerCase().trim();
        const n = (name.value || '').toLowerCase().trim();

        cards.forEach((card) => {{
          const passDecision = !d || card.dataset.decision === d;
          const passQa = !q || card.dataset.qa === q;
          const passChannel = !c || (card.dataset.channels || '').includes(c);
          const text = card.dataset.name + ' ' + card.querySelector('h3').textContent.toLowerCase();
          const passName = !n || text.includes(n);
          card.classList.toggle('hidden', !(passDecision && passQa && passChannel && passName));
        }});
      }}

      [decision, qa, channel, name].forEach((el) => el.addEventListener('input', applyFilters));
      applyFilters();
    }})();
  </script>
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
                "scores": qa_row.get("scores") or {},
                "weighted_score": qa_row.get("weighted_score"),
                "reject_reasons": qa_row.get("reject_reasons") or [],
                "reroll_final_status": reroll_status,
                "suggested_decision": decision,
                "decision_reason": reason,
                "entry_dimensions": entry.get("final_dimensions") or [],
                "entry_ratio": entry.get("requested_ratio") or entry.get("ratio"),
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
        reference_image_url=generation.get("reference_image_url"),
        export_manifest_path=export_path,
        decision_counts=decision_counts,
        qa_counts=qa_counts,
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
            "reference_image_url": generation.get("reference_image_url"),
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
