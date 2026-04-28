#!/usr/bin/env python3
"""Build human-review artifacts for a packet.

Outputs:
- human-review-template.json
- contact-sheet.html
- <packet>/index.html (magic-moment review frontend)
- artifact-pack-manifest.json
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from packet_utils import dump_json, ensure_packet_dir, load_json


def _scout_scraper_label(packet_dir: Path) -> str:
    """Render a one-line scout scraper provenance label for the review frontend."""
    scout_path = packet_dir / "scout.json"
    if not scout_path.exists():
        return "Scout: unknown"
    try:
        scout = json.loads(scout_path.read_text(encoding="utf-8"))
    except Exception:
        return "Scout: unknown"
    prov = scout.get("scrape_provenance") or {}
    name = prov.get("scraper") or scout.get("scraper") or "unknown"
    if name == "firecrawl":
        meta = prov.get("firecrawl_meta") or {}
        ms = meta.get("response_ms")
        credits = meta.get("credits_used")
        bits = ["Firecrawl /v2/scrape"]
        if ms:
            bits.append(f"{ms / 1000:.1f}s")
        if credits is not None:
            bits.append(f"~{credits} credit" + ("s" if credits != 1 else ""))
        return "Scout: " + " · ".join(bits)
    if name == "curl":
        return "Scout: curl"
    return f"Scout: {name}"


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


def decision_for(*, qa_status: str, reroll_final_status: str, image_exists: bool) -> Tuple[str, str]:
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


def parse_image_path(value: Any, packet: Path) -> Optional[Path]:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if not path.is_absolute():
        path = packet / path
    return path.resolve()


def format_dims(dimensions: List[int]) -> str:
    if len(dimensions) != 2:
        return "unknown"
    return f"{dimensions[0]} x {dimensions[1]}"


def run_status(decision_counts: Dict[str, int]) -> str:
    if decision_counts.get("reject", 0) > 0:
        return "Needs operator intervention"
    if decision_counts.get("reroll", 0) > 0:
        return "Review and reroll candidates ready"
    return "Ready for human approval"


def build_export_links(outputs: List[Dict[str, Any]], page_base: Path) -> str:
    if not outputs:
        return '<span class="muted">none</span>'
    links: List[str] = []
    for output in outputs[:4]:
        path_value = output.get("path")
        if not isinstance(path_value, str):
            continue
        path = Path(path_value)
        if not path.is_absolute():
            path = (page_base / path).resolve()
        href = html.escape(relpath(path, page_base))
        channel = html.escape(str(output.get("channel", "export")))
        dims = output.get("output_dimensions") or []
        ratio = output.get("ratio") or ratio_from_dimensions(dims)
        links.append(f'<a href="{href}" target="_blank" rel="noopener">{channel} ({html.escape(str(ratio))})</a>')
    return " ".join(links) if links else '<span class="muted">none</span>'


def row_card(row: Dict[str, Any], page_base: Path) -> str:
    reasons = row.get("reject_reasons") or []
    outputs = row.get("export_outputs") or []
    score = row.get("weighted_score")
    score_text = "n/a" if score is None else str(score)
    qa_status = str(row.get("qa_status", "unscored"))
    decision = str(row.get("suggested_decision", "reroll"))
    entry_dims = row.get("entry_dimensions") or []
    entry_ratio = str(row.get("entry_ratio") or ratio_from_dimensions(entry_dims))
    channels = ", ".join(str(x.get("channel", "")).lower() for x in outputs if x.get("channel")) or "none"

    top_output = outputs[0] if outputs else {}
    out_dims = top_output.get("output_dimensions") or []
    out_ratio = top_output.get("ratio") or ratio_from_dimensions(out_dims)
    render_mode = str(top_output.get("render_mode", "unknown"))

    reasons_html = "".join(f"<li>{html.escape(str(x))}</li>" for x in reasons[:4]) or "<li>none</li>"
    image_abs = parse_image_path(row.get("image_path"), page_base)
    img_src = html.escape(relpath(image_abs, page_base)) if image_abs and image_abs.exists() else ""

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
        f'<article class="card generated-image-card decision-{html.escape(decision)} qa-{html.escape(qa_status)}" '
        f'data-decision="{html.escape(decision)}" data-qa="{html.escape(qa_status)}" data-channels="{html.escape(channels)}" '
        f'data-name="{html.escape(str(row.get("shot_name", "")).lower())}">'
        '<div class="card-head">'
        f"<h3>{html.escape(str(row.get('asset_id', '')))} · {html.escape(str(row.get('shot_name', '')))}</h3>"
        '<div class="badges">'
        f'<span class="pill decision">{html.escape(decision)}</span>'
        f'<span class="pill qa">{html.escape(qa_status)}</span>'
        f'<span class="pill score">QA {html.escape(score_text)}</span>'
        "</div></div>"
        '<div class="media">'
        f'<img src="{img_src}" alt="{html.escape(str(row.get("asset_id", "")))}"/>'
        "</div>"
        '<dl class="meta">'
        f"<div><dt>Decision</dt><dd>{html.escape(str(row.get('decision_reason', '')))}</dd></div>"
        f"<div><dt>Source</dt><dd>{html.escape(format_dims(entry_dims))} ({html.escape(entry_ratio)})</dd></div>"
        f"<div><dt>Output</dt><dd>{html.escape(format_dims(out_dims))} ({html.escape(str(out_ratio))})</dd></div>"
        f"<div><dt>Render</dt><dd>{html.escape(render_mode)}</dd></div>"
        f"<div><dt>QA Breakdown</dt><dd>{html.escape(qa_breakdown)}</dd></div>"
        f"<div><dt>Exports</dt><dd>{build_export_links(outputs, page_base)}</dd></div>"
        "</dl>"
        '<div class="reasons"><strong>Top reasons</strong><ul>'
        f"{reasons_html}"
        "</ul></div>"
        "</article>"
    )


def build_gallery_html(
    *,
    packet: Path,
    page_base: Path,
    rows: List[Dict[str, Any]],
    scout: Dict[str, Any],
    generation: Dict[str, Any],
    reference_image: Optional[Path],
    reference_image_url: Optional[str],
    export_manifest_path: Path,
    decision_counts: Dict[str, int],
    qa_counts: Dict[str, int],
    primary_index: bool,
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    qa_summary = ", ".join(f"{k}: {v}" for k, v in sorted(qa_counts.items())) or "none"
    cards = "\n".join(row_card(row, page_base) for row in rows)

    brand = str(scout.get("brand_name") or scout.get("site_name") or "Unknown brand")
    product = str(scout.get("product_name") or scout.get("title") or "Unknown product")
    product_url = str(scout.get("url") or "")
    model = str(generation.get("model") or "unknown")
    provider = str(generation.get("provider") or "unknown")
    endpoint = str(generation.get("openai_image_endpoint") or "unknown")
    reference_path = str(reference_image) if reference_image else "none"
    run_log = packet / "live-proof-commands.log"

    ref_html = "<p class=\"muted\">Reference image: none</p>"
    if reference_image and reference_image.exists():
        ref_src = html.escape(relpath(reference_image, page_base))
        ref_html = (
            '<div class="reference-block">'
            "<h2>Reference Image</h2>"
            f'<img src="{ref_src}" alt="reference image"/>'
            f"<p><strong>Local:</strong> {html.escape(reference_path)}</p>"
            f"<p><strong>Source URL:</strong> {html.escape(reference_image_url or 'none')}</p>"
            "</div>"
        )

    magic_link = html.escape(relpath(packet / "index.html", page_base))
    contact_link = html.escape(relpath(packet / "assets" / "review" / "contact-sheet.html", page_base))
    packet_rel = html.escape(relpath(packet, page_base))

    primary_badge = "Magic Moment" if primary_index else "Legacy Contact Sheet"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Brand Shoot Kit Review Frontend</title>
  <style>
    :root {{
      --bg: #0d121a;
      --panel: #141d2a;
      --panel-soft: #1a2636;
      --ink: #f4f7fb;
      --muted: #9fb2c9;
      --line: #2d3e56;
      --ok: #47d98d;
      --warn: #ffc066;
      --bad: #ff7b7b;
      --accent: #7dd3fc;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); font-family: "Space Grotesk", "Avenir Next", sans-serif; background: radial-gradient(circle at 10% 5%, #1f2b3b 0, var(--bg) 45%), linear-gradient(150deg, #0d121a 0, #111a25 100%); }}
    a {{ color: #9cd9ff; }}
    .shell {{ max-width: 1320px; margin: 0 auto; padding: 24px 18px 40px; }}
    .hero {{ border: 1px solid var(--line); background: linear-gradient(145deg, rgba(125,211,252,0.14), rgba(71,217,141,0.08) 35%, rgba(20,29,42,0.9) 100%); border-radius: 18px; padding: 18px; display: grid; gap: 14px; grid-template-columns: 2fr 1fr; }}
    .hero h1 {{ margin: 0; font-size: clamp(26px, 3vw, 38px); line-height: 1.04; }}
    .hero p {{ margin: 6px 0 0; color: var(--muted); }}
    .hero-grid {{ display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 12px; }}
    .kpi {{ background: rgba(20,29,42,0.86); border: 1px solid var(--line); border-radius: 12px; padding: 10px; }}
    .kpi .label {{ font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 0.08em; }}
    .kpi .value {{ font-size: 24px; margin-top: 4px; font-weight: 700; }}
    .kpi.approve .value {{ color: var(--ok); }}
    .kpi.reroll .value {{ color: var(--warn); }}
    .kpi.reject .value {{ color: var(--bad); }}
    .kpi.total .value {{ color: var(--accent); }}
    .pill {{ display: inline-flex; padding: 3px 10px; border-radius: 999px; border: 1px solid var(--line); background: rgba(13,18,26,0.8); font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; }}
    .panel {{ border: 1px solid var(--line); background: var(--panel); border-radius: 16px; padding: 14px; }}
    .panel h2 {{ margin: 0 0 8px; font-size: 16px; }}
    .meta-list {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }}
    .meta-list li {{ font-size: 13px; color: var(--muted); }}
    .reference-block img {{ width: 100%; border-radius: 12px; border: 1px solid var(--line); background: #fff; max-height: 280px; object-fit: contain; }}
    .reference-block p {{ margin: 8px 0 0; font-size: 12px; color: var(--muted); }}
    .toolbar {{ margin-top: 14px; display: grid; gap: 8px; grid-template-columns: 1fr 1fr 1fr 2fr; }}
    .toolbar select, .toolbar input {{ width: 100%; border-radius: 10px; border: 1px solid var(--line); background: var(--panel-soft); color: var(--ink); padding: 10px; font-size: 13px; }}
    .gallery {{ margin-top: 14px; display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); }}
    .card {{ border: 1px solid var(--line); border-radius: 14px; background: var(--panel); padding: 10px; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }}
    .card-head h3 {{ margin: 0; font-size: 14px; line-height: 1.25; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: end; }}
    .decision-approve .pill.decision {{ border-color: rgba(71,217,141,0.4); color: var(--ok); }}
    .decision-reroll .pill.decision {{ border-color: rgba(255,192,102,0.5); color: var(--warn); }}
    .decision-reject .pill.decision {{ border-color: rgba(255,123,123,0.5); color: var(--bad); }}
    .media {{ margin-top: 10px; }}
    .media img {{ width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: #0d121a; border: 1px solid var(--line); border-radius: 12px; }}
    .meta {{ margin-top: 8px; display: grid; gap: 5px; }}
    .meta div {{ display: grid; grid-template-columns: 118px 1fr; gap: 8px; font-size: 12px; }}
    .meta dt {{ color: var(--muted); }}
    .meta dd {{ margin: 0; }}
    .reasons {{ margin-top: 8px; font-size: 12px; color: var(--muted); }}
    .reasons ul {{ margin: 4px 0 0 16px; padding: 0; }}
    .hidden {{ display: none !important; }}
    .stack {{ display: grid; gap: 12px; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 1040px) {{
      .hero {{ grid-template-columns: 1fr; }}
      .toolbar {{ grid-template-columns: 1fr 1fr; }}
      .hero-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 640px) {{
      .toolbar {{ grid-template-columns: 1fr; }}
      .gallery {{ grid-template-columns: 1fr; }}
      .meta div {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell" data-bsk-magic-moment="true" data-frontend-marker="generated-review-frontend">
    <section class="hero">
      <div>
        <span class="pill">{html.escape(primary_badge)}</span>
        <h1>{html.escape(brand)} · {html.escape(product)}</h1>
        <p>{html.escape(run_status(decision_counts))}</p>
        <p><strong>Product URL:</strong> <a href="{html.escape(product_url)}">{html.escape(product_url or 'none')}</a></p>
        <div class="hero-grid">
          <div class="kpi total"><div class="label">Generated</div><div class="value">{len(rows)}</div></div>
          <div class="kpi approve"><div class="label">Suggest Approve</div><div class="value">{decision_counts.get('approve', 0)}</div></div>
          <div class="kpi reroll"><div class="label">Suggest Reroll</div><div class="value">{decision_counts.get('reroll', 0)}</div></div>
          <div class="kpi reject"><div class="label">Suggest Reject</div><div class="value">{decision_counts.get('reject', 0)}</div></div>
        </div>
      </div>
      <div class="stack">
        <section class="panel">
          <h2>Open Links</h2>
          <ul class="meta-list">
            <li><a href="{magic_link}">Magic moment index.html</a></li>
            <li><a href="{contact_link}">Legacy contact-sheet.html</a></li>
            <li>Packet root: <code>{packet_rel}</code></li>
          </ul>
        </section>
        <section class="panel">
          {ref_html}
        </section>
      </div>
    </section>

    <section class="panel" style="margin-top:14px;">
      <h2>Provenance Summary</h2>
      <ul class="meta-list">
        <li><strong>Generated At:</strong> {html.escape(timestamp)}</li>
        <li><strong>Provider:</strong> {html.escape(provider)}</li>
        <li><strong>Model:</strong> {html.escape(model)}</li>
        <li><strong>Image Endpoint:</strong> {html.escape(endpoint)}</li>
        <li><strong>Export Manifest:</strong> {html.escape(str(export_manifest_path))}</li>
        <li><strong>Command Log:</strong> {html.escape(str(run_log))} ({'present' if run_log.exists() else 'missing'})</li>
        <li><strong>QA Mix:</strong> {html.escape(qa_summary)}</li>
        <li><strong>{html.escape(_scout_scraper_label(packet))}</strong></li>
      </ul>
    </section>

    <section class="toolbar panel" style="margin-top:14px;">
      <select id="filter-decision">
        <option value="">All decisions</option>
        <option value="approve">Approve</option>
        <option value="reroll">Reroll</option>
        <option value="reject">Reject</option>
      </select>
      <select id="filter-qa">
        <option value="">All QA statuses</option>
        <option value="pass">pass</option>
        <option value="manual_review">manual_review</option>
        <option value="fail">fail</option>
        <option value="unscored">unscored</option>
      </select>
      <input id="filter-channel" type="text" placeholder="Filter channel (pdp, social, amazon...)" />
      <input id="filter-name" type="text" placeholder="Filter shot name or asset id" />
    </section>

    <section id="generated-gallery" class="gallery" data-gallery="generated-images" data-card-count="{len(rows)}">
      {cards}
    </section>
  </div>

  <script>
    (function () {{
      const cards = Array.from(document.querySelectorAll('.generated-image-card'));
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
          const text = (card.dataset.name || '') + ' ' + (card.querySelector('h3')?.textContent || '').toLowerCase();
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
    scout_path = packet / "scout.json"
    scout = load_json(scout_path) if scout_path.exists() else {}

    qa_by_asset = qa_index(qa)
    reroll_by_asset = reroll_index(reroll)
    export_by_asset = export_index(export_manifest)

    rows: List[Dict[str, Any]] = []
    decision_counts = {"approve": 0, "reroll": 0, "reject": 0}
    qa_counts: Dict[str, int] = {}

    for entry in generation.get("entries", []):
        asset_id = str(entry.get("asset_id", ""))
        shot_name = str(entry.get("shot_name", asset_id))
        image_path = parse_image_path(entry.get("image_path", ""), packet)
        qa_row = qa_by_asset.get(asset_id, {})
        reroll_row = reroll_by_asset.get(asset_id, {})
        export_row = export_by_asset.get(asset_id, {})

        qa_status = str(qa_row.get("status", "unscored"))
        reroll_status = str(reroll_row.get("final_status", "not_run"))
        decision, reason = decision_for(
            qa_status=qa_status,
            reroll_final_status=reroll_status,
            image_exists=bool(image_path and image_path.exists()),
        )
        decision_counts[decision] += 1
        qa_counts[qa_status] = qa_counts.get(qa_status, 0) + 1

        rows.append(
            {
                "asset_id": asset_id,
                "shot_name": shot_name,
                "image_path": str(image_path) if image_path else "",
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
    reference_image = parse_image_path(reference_image_path, packet) if reference_image_path else None
    if reference_image and not reference_image.exists():
        reference_image = None

    template_path = out_dir / "human-review-template.json"
    contact_path = out_dir / "contact-sheet.html"
    magic_index_path = packet / "index.html"
    manifest_path = out_dir / "artifact-pack-manifest.json"

    template = {
        "review_meta": {
            "review_date": "YYYY-MM-DD",
            "reviewer": "Name",
            "packet_dir": str(packet),
            "product_url": str(scout.get("url", "")),
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

    magic_html = build_gallery_html(
        packet=packet,
        page_base=packet,
        rows=rows,
        scout=scout,
        generation=generation,
        reference_image=reference_image,
        reference_image_url=generation.get("reference_image_url"),
        export_manifest_path=export_path,
        decision_counts=decision_counts,
        qa_counts=qa_counts,
        primary_index=True,
    )
    contact_html = build_gallery_html(
        packet=packet,
        page_base=out_dir,
        rows=rows,
        scout=scout,
        generation=generation,
        reference_image=reference_image,
        reference_image_url=generation.get("reference_image_url"),
        export_manifest_path=export_path,
        decision_counts=decision_counts,
        qa_counts=qa_counts,
        primary_index=False,
    )
    magic_index_path.write_text(magic_html, encoding="utf-8")
    contact_path.write_text(contact_html, encoding="utf-8")

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
            "magic_index_html": str(magic_index_path),
        },
        "summary": {
            "total_assets": len(rows),
            "qa_status_counts": qa_counts,
            "suggested_decisions": decision_counts,
            "packaged_for_review": len(rows),
        },
        "artifacts": {
            "magic_index_html": str(magic_index_path),
            "human_review_template": str(template_path),
            "contact_sheet_html": str(contact_path),
        },
    }
    dump_json(manifest_path, manifest)
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
