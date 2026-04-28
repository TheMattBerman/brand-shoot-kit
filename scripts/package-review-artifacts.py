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
    resolved = path.resolve()
    if resolved.exists():
        return resolved
    # Manifests sometimes carry absolute paths from another machine; if the file
    # isn't there, fall back to the same basename inside this packet.
    candidate = (packet / "assets" / "generated" / path.name).resolve()
    if candidate.exists():
        return candidate
    return resolved


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
        return '<span class="muted">—</span>'
    links: List[str] = []
    for output in outputs[:6]:
        path_value = output.get("path")
        if not isinstance(path_value, str):
            continue
        path = Path(path_value)
        if not path.is_absolute():
            path = (page_base / path).resolve()
        href = html.escape(relpath(path, page_base))
        channel = html.escape(str(output.get("channel", "export")).lower())
        dims = output.get("output_dimensions") or []
        ratio = output.get("ratio") or ratio_from_dimensions(dims)
        links.append(
            f'<a class="export-link" href="{href}" target="_blank" rel="noopener">'
            f'<span class="ch">{channel}</span><span class="rt">{html.escape(str(ratio))}</span></a>'
        )
    return " ".join(links) if links else '<span class="muted">—</span>'


_RATIO_GLYPHS: Dict[str, Tuple[int, int]] = {
    "1:1": (14, 14),
    "4:5": (12, 15),
    "9:16": (10, 16),
    "16:9": (16, 9),
}


def ratio_glyph_svg(ratio: str) -> str:
    """Return a small inline SVG glyph that visually encodes an aspect ratio."""
    w, h = _RATIO_GLYPHS.get(ratio, (14, 14))
    # center inside an 18x18 box
    x = (18 - w) / 2
    y = (18 - h) / 2
    return (
        f'<svg class="ratio-glyph" viewBox="0 0 18 18" aria-hidden="true">'
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" '
        f'fill="none" stroke="currentColor" stroke-width="1"/>'
        f'</svg>'
    )


_DECISION_MARK: Dict[str, Tuple[str, str]] = {
    # (mark glyph, label)
    "approve": ("◉", "stet"),
    "reroll": ("◐", "rework"),
    "reject": ("✕", "kill"),
}


def score_sparkline(scores: Dict[str, Any]) -> str:
    """Render the six QA criteria as a tiny vertical-bar sparkline."""
    keys = [
        ("PA", "product_accuracy"),
        ("CU", "commerce_usefulness"),
        ("BF", "brand_fit"),
        ("SR", "scene_realism"),
        ("VC", "visual_clarity"),
        ("AR", "artifact_risk"),
    ]
    bars = []
    for label, key in keys:
        raw = scores.get(key)
        if raw is None:
            value = 0
        else:
            try:
                value = max(0, min(100, int(raw)))
            except (TypeError, ValueError):
                value = 0
        bars.append(
            f'<span class="sb"><span class="sb-bar" style="height:{value}%"></span>'
            f'<span class="sb-lbl">{label}</span><span class="sb-num">{value if raw is not None else "—"}</span></span>'
        )
    return f'<div class="sparkline" role="img" aria-label="QA score breakdown">{"".join(bars)}</div>'


def row_card(row: Dict[str, Any], page_base: Path, plate_index: int) -> str:
    reasons = row.get("reject_reasons") or []
    outputs = row.get("export_outputs") or []
    score = row.get("weighted_score")
    score_text = "—" if score is None else str(score)
    qa_status = str(row.get("qa_status", "unscored"))
    decision = str(row.get("suggested_decision", "reroll"))
    entry_dims = row.get("entry_dimensions") or []
    entry_ratio = str(row.get("entry_ratio") or ratio_from_dimensions(entry_dims))
    channels = ", ".join(str(x.get("channel", "")).lower() for x in outputs if x.get("channel")) or "none"

    top_output = outputs[0] if outputs else {}
    out_dims = top_output.get("output_dimensions") or []
    out_ratio = str(top_output.get("ratio") or ratio_from_dimensions(out_dims))
    render_mode = str(top_output.get("render_mode", "—"))
    use_case = str(row.get("use_case") or "").upper()

    reasons_html = (
        "".join(f"<li>{html.escape(str(x))}</li>" for x in reasons[:4])
        if reasons
        else '<li class="muted">no flags raised</li>'
    )
    image_abs = parse_image_path(row.get("image_path"), page_base)
    img_src = html.escape(relpath(image_abs, page_base)) if image_abs and image_abs.exists() else ""

    scores = row.get("scores") or {}
    sparkline_html = score_sparkline(scores)

    asset_id = str(row.get("asset_id", ""))
    shot_name = str(row.get("shot_name", ""))
    plate_no = f"{plate_index:02d}"
    decision_mark, decision_label = _DECISION_MARK.get(decision, ("◐", decision))

    aspect_css = entry_ratio.replace(":", " / ") if ":" in entry_ratio else "1 / 1"

    return (
        f'<article class="plate generated-image-card decision-{html.escape(decision)} qa-{html.escape(qa_status)}" '
        f'data-decision="{html.escape(decision)}" data-qa="{html.escape(qa_status)}" '
        f'data-channels="{html.escape(channels)}" '
        f'data-name="{html.escape(shot_name.lower())}" '
        f'data-ratio="{html.escape(entry_ratio)}" '
        f'style="--plate-aspect: {html.escape(aspect_css)};">'
        '<div class="plate-eyebrow">'
        f'<span class="plate-no">Plate Nº {plate_no}</span>'
        f'<span class="plate-sep">·</span>'
        f'<span class="plate-ratio">{ratio_glyph_svg(entry_ratio)}<em>{html.escape(entry_ratio)}</em></span>'
        f'<span class="plate-sep">·</span>'
        f'<span class="plate-usecase">{html.escape(use_case or "—")}</span>'
        '<span class="plate-spacer"></span>'
        f'<span class="plate-mark mark-{html.escape(decision)}" title="{html.escape(decision_label)}">'
        f'<span class="mark-glyph">{decision_mark}</span>'
        f'<span class="mark-text">{html.escape(decision_label)}</span>'
        '</span>'
        '</div>'
        '<div class="plate-frame">'
        f'<span class="plate-bignum" aria-hidden="true">{plate_no}</span>'
        '<div class="plate-mat">'
        f'<img class="plate-img" src="{img_src}" alt="{html.escape(asset_id)} — {html.escape(shot_name)}" loading="lazy"/>'
        '</div>'
        '</div>'
        '<div class="plate-caption">'
        f'<h3 class="plate-title">{html.escape(shot_name or asset_id)}</h3>'
        f'<p class="plate-subtitle"><span class="mono">{html.escape(asset_id)}</span> · '
        f'weighted <span class="qa-num">{html.escape(score_text)}</span> · '
        f'<span class="qa-status qa-{html.escape(qa_status)}">{html.escape(qa_status.replace("_", " "))}</span></p>'
        '</div>'
        f'{sparkline_html}'
        '<div class="plate-body">'
        '<dl class="plate-meta">'
        f'<div><dt>Decision</dt><dd>{html.escape(str(row.get("decision_reason", "—")))}</dd></div>'
        f'<div><dt>Source</dt><dd>{html.escape(format_dims(entry_dims))} <span class="muted">({html.escape(entry_ratio)})</span></dd></div>'
        f'<div><dt>Output</dt><dd>{html.escape(format_dims(out_dims))} <span class="muted">({html.escape(out_ratio)})</span></dd></div>'
        f'<div><dt>Render</dt><dd class="mono">{html.escape(render_mode)}</dd></div>'
        '</dl>'
        '<div class="plate-reasons">'
        '<span class="plate-reasons-label">Field notes</span>'
        f'<ul>{reasons_html}</ul>'
        '</div>'
        '<div class="plate-exports">'
        '<span class="plate-exports-label">Exports</span>'
        f'<div class="export-links">{build_export_links(outputs, page_base)}</div>'
        '</div>'
        '</div>'
        '</article>'
    )


def _hash_dossier_no(packet: Path) -> str:
    """Stable, fun-looking dossier number derived from the packet path."""
    import hashlib

    digest = hashlib.sha1(str(packet).encode("utf-8")).hexdigest().upper()
    return f"{digest[:4]}-{digest[4:8]}"


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
    timestamp_pretty = datetime.now(UTC).strftime("%d %b %Y · %H:%M UTC").upper()
    qa_summary = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(qa_counts.items())) or "none"
    cards = "\n".join(row_card(row, page_base, idx + 1) for idx, row in enumerate(rows))

    brand = str(scout.get("brand_name") or scout.get("site_name") or "Unattributed Studio")
    product = str(scout.get("product_name") or scout.get("title") or "Untitled Subject")
    product_url = str(scout.get("url") or "")
    model = str(generation.get("model") or "unknown")
    provider = str(generation.get("provider") or "unknown")
    endpoint = str(generation.get("openai_image_endpoint") or "—")
    run_id = str(generation.get("run_id") or "—")
    reference_path = str(reference_image) if reference_image else "none"
    run_log = packet / "live-proof-commands.log"
    dossier_no = _hash_dossier_no(packet)

    total = len(rows)
    approve_n = decision_counts.get("approve", 0)
    reroll_n = decision_counts.get("reroll", 0)
    reject_n = decision_counts.get("reject", 0)
    status_text = run_status(decision_counts)

    # status-condition class drives accent on the "VERDICT" stamp
    if reject_n > 0:
        verdict_class, verdict_word = "verdict-hold", "HOLD"
    elif reroll_n > 0:
        verdict_class, verdict_word = "verdict-mixed", "REVIEW"
    else:
        verdict_class, verdict_word = "verdict-go", "READY"

    # Reference plate
    if reference_image and reference_image.exists():
        ref_src = html.escape(relpath(reference_image, page_base))
        ref_block = (
            '<figure class="ref-plate">'
            '<div class="ref-frame">'
            f'<img src="{ref_src}" alt="source reference"/>'
            '<span class="ref-stamp">SOURCE</span>'
            '</div>'
            '<figcaption>'
            '<span class="ref-eyebrow">Plate Nº 00 — Reference</span>'
            '<p class="ref-quote">'
            '“Every frame in this dossier is rendered against the source artwork at right. '
            'Product truth is non-negotiable.”'
            '</p>'
            f'<dl class="ref-meta">'
            f'<div><dt>Local</dt><dd class="mono">{html.escape(reference_path)}</dd></div>'
            f'<div><dt>Source</dt><dd class="mono">{html.escape(reference_image_url or "—")}</dd></div>'
            '</dl>'
            '</figcaption>'
            '</figure>'
        )
    else:
        ref_block = (
            '<figure class="ref-plate ref-plate--empty">'
            '<div class="ref-frame ref-frame--empty"><span class="ref-stamp">NO REF</span></div>'
            '<figcaption>'
            '<span class="ref-eyebrow">Plate Nº 00 — Reference</span>'
            '<p class="ref-quote">No real product reference was available for this run. '
            'Generated frames below are unverified against source artwork.</p>'
            '</figcaption>'
            '</figure>'
        )

    magic_link = html.escape(relpath(packet / "index.html", page_base))
    contact_link = html.escape(relpath(packet / "assets" / "review" / "contact-sheet.html", page_base))
    packet_rel = html.escape(relpath(packet, page_base))
    primary_badge = "Studio Proof" if primary_index else "Contact Sheet"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="color-scheme" content="light"/>
  <title>{html.escape(brand)} · {html.escape(product)} — Brand Shoot Dossier</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..900,0..100,0..1;1,9..144,300..900,0..100,0..1&family=Geist+Mono:wght@300;400;500;600&family=Inter+Tight:wght@300;400;500;600&display=swap">
  <style>
    :root {{
      --paper:        #f1ece1;
      --paper-warm:   #ece4cf;
      --paper-deep:   #e3d9bf;
      --ink:          #15120c;
      --ink-soft:     #3a352a;
      --ink-faint:    #6f6857;
      --rule:         #c8bea1;
      --rule-soft:    #d8cfb5;
      --mute:         #8d846f;
      --vermilion:    #b8401a;
      --vermilion-deep: #8e2f12;
      --moss:         #4a6045;
      --ochre:        #9c6e1a;
      --bignum:       rgba(21,18,12,0.06);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{
      color: var(--ink);
      background: var(--paper);
      font-family: "Inter Tight", "Helvetica Neue", system-ui, sans-serif;
      font-feature-settings: "ss01", "ss02", "cv11";
      font-size: 15px;
      line-height: 1.55;
      letter-spacing: 0.005em;
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
      background-color: var(--paper);
      background-image:
        radial-gradient(at 8% 0%, rgba(184, 64, 26, 0.07), transparent 38%),
        radial-gradient(at 95% 4%, rgba(74, 96, 69, 0.06), transparent 42%),
        radial-gradient(at 50% 100%, rgba(184, 64, 26, 0.04), transparent 55%);
      background-repeat: no-repeat;
      background-attachment: fixed;
      min-height: 100vh;
      position: relative;
    }}
    /* Paper-warm tonal layering — subtle bands that read as printed cream
       without the SVG filter that breaks Chrome full-page screenshots. */
    .grain {{ display: none; }}
    .shell {{ position: relative; z-index: 2; max-width: 1340px; margin: 0 auto; padding: 28px 36px 80px; }}
    a {{ color: var(--ink); text-decoration-color: var(--rule); text-underline-offset: 3px; transition: text-decoration-color .25s ease, color .25s ease; }}
    a:hover {{ color: var(--vermilion); text-decoration-color: var(--vermilion); }}
    .mono {{ font-family: "Geist Mono", ui-monospace, monospace; font-size: 0.86em; letter-spacing: 0.01em; }}
    .muted {{ color: var(--mute); }}

    /* ─── Top utility bar ─────────────────────────────────────────────────── */
    .colophon-bar {{
      display: flex; align-items: center; gap: 20px;
      font-family: "Geist Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--ink-soft);
      padding-bottom: 16px;
      border-bottom: 1px solid var(--rule);
    }}
    .colophon-bar .dot {{
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--vermilion); display: inline-block;
      box-shadow: 0 0 0 3px rgba(184,64,26,0.18);
    }}
    .colophon-bar .spacer {{ flex: 1; }}
    .colophon-bar .pill {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 4px 10px;
      border: 1px solid var(--rule);
      border-radius: 999px;
      background: rgba(255,255,255,0.4);
    }}

    /* ─── Masthead ────────────────────────────────────────────────────────── */
    .masthead {{
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
      gap: 56px;
      padding: 44px 0 36px;
      border-bottom: 1px solid var(--rule);
    }}
    .masthead-eyebrow {{
      font-family: "Geist Mono", monospace;
      font-size: 11px; letter-spacing: 0.22em;
      text-transform: uppercase; color: var(--ink-soft);
      display: flex; align-items: center; gap: 14px;
      margin-bottom: 28px;
    }}
    .masthead-eyebrow .rule {{ flex: 1; height: 1px; background: var(--rule); }}
    .masthead h1 {{
      font-family: "Fraunces", "Times New Roman", serif;
      font-variation-settings: "opsz" 144, "SOFT" 0, "WONK" 1;
      font-weight: 360;
      font-size: clamp(48px, 7vw, 96px);
      line-height: 0.94;
      letter-spacing: -0.025em;
      margin: 0;
      color: var(--ink);
    }}
    .masthead h1 .product {{
      display: block;
      font-style: italic;
      font-variation-settings: "opsz" 144, "SOFT" 100, "WONK" 1;
      font-weight: 300;
      color: var(--ink-soft);
      margin-top: 8px;
      font-size: 0.78em;
    }}
    .masthead-url {{
      font-family: "Geist Mono", monospace;
      font-size: 12px;
      color: var(--ink-soft);
      margin-top: 28px;
      display: inline-block;
      letter-spacing: 0.02em;
      border-bottom: 1px solid var(--rule);
      padding-bottom: 4px;
    }}
    .masthead-status {{
      margin-top: 22px;
      display: flex; align-items: baseline; gap: 12px;
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 32, "SOFT" 0;
      font-style: italic;
      font-weight: 320;
      font-size: 19px;
      color: var(--ink-soft);
    }}
    .masthead-status::before {{
      content: ""; width: 24px; height: 1px; background: var(--vermilion); display: inline-block;
    }}

    /* Studio index card (right column) */
    .studio-card {{
      align-self: start;
      border: 1px solid var(--ink);
      background: var(--paper-warm);
      padding: 22px 24px 26px;
      position: relative;
      box-shadow: 6px 6px 0 0 var(--paper-deep);
    }}
    .studio-card::before {{
      content: "";
      position: absolute;
      top: -1px; left: 18px; right: 18px;
      height: 6px;
      background:
        repeating-linear-gradient(90deg, var(--ink) 0 8px, transparent 8px 14px);
      opacity: 0.12;
    }}
    .studio-card-hd {{
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.24em; text-transform: uppercase;
      color: var(--ink-soft); margin-bottom: 14px;
      display: flex; justify-content: space-between;
    }}
    .studio-card dl {{ margin: 0; display: grid; gap: 8px; }}
    .studio-card dl > div {{
      display: grid; grid-template-columns: 88px 1fr; gap: 14px;
      padding-bottom: 8px;
      border-bottom: 1px dashed var(--rule-soft);
    }}
    .studio-card dl > div:last-child {{ border-bottom: 0; padding-bottom: 0; }}
    .studio-card dt {{
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
      color: var(--mute);
      align-self: center;
    }}
    .studio-card dd {{
      margin: 0;
      font-family: "Geist Mono", monospace;
      font-size: 12px;
      color: var(--ink);
      word-break: break-all;
    }}

    /* ─── Verdict stamp (rotated) ─────────────────────────────────────────── */
    .verdict-stamp {{
      position: absolute;
      top: 32px; right: -8px;
      transform: rotate(-7deg);
      border: 2px solid var(--vermilion);
      color: var(--vermilion);
      padding: 10px 18px 8px;
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 96, "SOFT" 0, "WONK" 1;
      font-weight: 600;
      font-size: 22px;
      letter-spacing: 0.18em;
      line-height: 1;
      background: rgba(241,236,225,0.6);
      box-shadow: inset 0 0 0 1px var(--vermilion);
      text-transform: uppercase;
      pointer-events: none;
      filter: drop-shadow(0 0 0.5px rgba(184,64,26,0.4));
      animation: stampDrop .9s cubic-bezier(.2,.9,.3,1.4) both;
      animation-delay: 1.1s;
    }}
    .verdict-stamp::after {{
      content: "·";
      display: block;
      font-size: 9px;
      letter-spacing: 0.4em;
      margin-top: 2px;
      opacity: 0.85;
    }}
    .verdict-stamp .verdict-sub {{
      display: block;
      font-family: "Geist Mono", monospace;
      font-size: 8px; font-weight: 500;
      letter-spacing: 0.32em;
      margin-top: 4px;
      opacity: 0.75;
    }}
    .verdict-go     {{ border-color: var(--moss); color: var(--moss); box-shadow: inset 0 0 0 1px var(--moss); }}
    .verdict-mixed  {{ border-color: var(--vermilion); color: var(--vermilion); box-shadow: inset 0 0 0 1px var(--vermilion); }}
    .verdict-hold   {{ border-color: var(--ink); color: var(--ink); box-shadow: inset 0 0 0 1px var(--ink); }}
    @keyframes stampDrop {{
      0% {{ transform: rotate(8deg) scale(1.4); opacity: 0; }}
      60% {{ transform: rotate(-9deg) scale(0.94); opacity: 1; }}
      100% {{ transform: rotate(-7deg) scale(1); opacity: 1; }}
    }}

    /* ─── Ledger row (KPI) ────────────────────────────────────────────────── */
    .ledger {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0;
      margin: 36px 0 12px;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
    }}
    .ledger-cell {{
      padding: 22px 0 24px;
      border-right: 1px solid var(--rule-soft);
      position: relative;
    }}
    .ledger-cell:last-child {{ border-right: 0; }}
    .ledger-cell .label {{
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
      color: var(--mute);
      display: block; margin-bottom: 6px;
    }}
    .ledger-cell .num {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 144, "SOFT" 0, "WONK" 1;
      font-weight: 280;
      font-size: clamp(48px, 6vw, 76px);
      line-height: 1;
      letter-spacing: -0.02em;
      color: var(--ink);
    }}
    .ledger-cell.approve .num {{ color: var(--moss); }}
    .ledger-cell.reroll .num {{ color: var(--vermilion); }}
    .ledger-cell.reject .num {{ color: var(--ink); }}
    .ledger-cell .delta {{
      font-family: "Geist Mono", monospace;
      font-size: 11px; color: var(--mute); margin-top: 8px; display: block;
      letter-spacing: 0.04em;
    }}

    /* ─── Reference plate ─────────────────────────────────────────────────── */
    .ref-plate {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
      gap: 48px;
      align-items: center;
      margin: 56px 0 8px;
      padding: 36px 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      position: relative;
    }}
    .ref-frame {{
      background: var(--paper-warm);
      padding: 28px;
      position: relative;
      box-shadow: 0 1px 0 var(--rule), 0 24px 40px -32px rgba(21,18,12,0.45);
    }}
    .ref-frame::after {{
      content: "";
      position: absolute; inset: 14px;
      border: 1px solid var(--rule);
      pointer-events: none;
    }}
    .ref-frame img {{
      display: block; width: 100%; height: auto;
      max-height: 460px; object-fit: contain;
      background: #fff;
      filter: contrast(1.02);
    }}
    .ref-frame--empty {{
      aspect-ratio: 4 / 3;
      display: flex; align-items: center; justify-content: center;
      color: var(--mute);
    }}
    .ref-stamp {{
      position: absolute;
      top: 14px; left: 14px;
      font-family: "Geist Mono", monospace;
      font-size: 9px; letter-spacing: 0.32em;
      padding: 3px 8px;
      background: var(--ink); color: var(--paper);
      text-transform: uppercase;
      z-index: 2;
    }}
    .ref-eyebrow {{
      font-family: "Geist Mono", monospace;
      font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase;
      color: var(--ink-soft); display: block; margin-bottom: 14px;
    }}
    .ref-quote {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 80, "SOFT" 50, "WONK" 1;
      font-style: italic;
      font-weight: 320;
      font-size: clamp(20px, 2vw, 26px);
      line-height: 1.32;
      color: var(--ink);
      margin: 0 0 22px;
      max-width: 36ch;
    }}
    .ref-meta {{ display: grid; gap: 10px; margin: 0; max-width: 480px; }}
    .ref-meta > div {{ display: grid; grid-template-columns: 70px 1fr; gap: 14px; padding-bottom: 8px; border-bottom: 1px dashed var(--rule-soft); }}
    .ref-meta dt {{ font-family: "Geist Mono", monospace; font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--mute); }}
    .ref-meta dd {{ margin: 0; font-size: 12px; word-break: break-all; }}

    /* ─── Index / filter bar ─────────────────────────────────────────────── */
    .index-bar {{
      margin-top: 52px;
      padding: 18px 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      display: grid;
      grid-template-columns: 200px repeat(3, minmax(0, 1fr)) minmax(0, 1.5fr);
      gap: 24px;
      align-items: center;
    }}
    .index-bar-title {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 32, "SOFT" 0;
      font-style: italic;
      font-weight: 320;
      font-size: 22px;
      color: var(--ink);
    }}
    .index-bar-title small {{
      display: block;
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
      color: var(--mute); font-style: normal;
      margin-top: 4px;
    }}
    .index-bar label {{
      display: block;
      font-family: "Geist Mono", monospace;
      font-size: 9px; letter-spacing: 0.24em; text-transform: uppercase;
      color: var(--mute);
      margin-bottom: 6px;
    }}
    .index-bar select, .index-bar input {{
      width: 100%;
      background: transparent;
      border: 0;
      border-bottom: 1px solid var(--ink);
      padding: 6px 0 8px;
      font-family: "Geist Mono", monospace;
      font-size: 13px;
      color: var(--ink);
      outline: none;
      -webkit-appearance: none;
      appearance: none;
      border-radius: 0;
      letter-spacing: 0.02em;
    }}
    .index-bar select {{ background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%2315120c' fill='none' stroke-width='1.2'/></svg>"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 18px; }}
    .index-bar input::placeholder {{ color: var(--mute); }}
    .index-bar select:focus, .index-bar input:focus {{ border-bottom-color: var(--vermilion); }}

    /* ─── Plate gallery ──────────────────────────────────────────────────── */
    .plates {{
      margin-top: 36px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 64px 56px;
    }}
    @media (min-width: 1180px) {{ .plates {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    .plate {{
      position: relative;
      padding-top: 20px;
      border-top: 1px solid var(--rule);
      animation: plateFadeIn .85s cubic-bezier(.2,.7,.3,1) both;
      animation-delay: calc(0.06s * var(--i, 0));
    }}
    @keyframes plateFadeIn {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .plate-eyebrow {{
      display: flex; align-items: center; gap: 12px;
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
      color: var(--ink-soft);
      margin-bottom: 14px;
    }}
    .plate-eyebrow .plate-sep {{ color: var(--rule); }}
    .plate-eyebrow .plate-spacer {{ flex: 1; }}
    .plate-ratio {{ display: inline-flex; align-items: center; gap: 6px; }}
    .plate-ratio em {{ font-style: normal; }}
    .ratio-glyph {{ width: 14px; height: 14px; color: var(--ink-soft); }}
    .plate-mark {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 3px 9px;
      border: 1px solid currentColor;
      border-radius: 2px;
      letter-spacing: 0.24em;
    }}
    .plate-mark .mark-glyph {{ font-size: 13px; line-height: 1; }}
    .mark-approve {{ color: var(--moss); }}
    .mark-reroll  {{ color: var(--vermilion); }}
    .mark-reject  {{ color: var(--ink); background: rgba(21,18,12,0.04); }}

    .plate-frame {{
      position: relative;
      overflow: visible;
      isolation: isolate;
    }}
    .plate-bignum {{
      position: absolute;
      top: -8px; left: -14px;
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 144, "SOFT" 0, "WONK" 1;
      font-weight: 280;
      font-style: italic;
      font-size: clamp(160px, 22vw, 280px);
      line-height: 0.78;
      color: var(--bignum);
      pointer-events: none;
      z-index: 0;
      letter-spacing: -0.05em;
      user-select: none;
    }}
    .plate-mat {{
      position: relative;
      z-index: 1;
      background: var(--paper-warm);
      padding: 22px;
      box-shadow:
        0 1px 0 0 var(--rule),
        0 30px 50px -40px rgba(21,18,12,0.55);
    }}
    .plate-mat::after {{
      content: "";
      position: absolute; inset: 10px;
      border: 1px solid var(--rule);
      pointer-events: none;
    }}
    .plate-img {{
      display: block;
      width: 100%;
      aspect-ratio: var(--plate-aspect, 1 / 1);
      object-fit: contain;
      background: #fff;
      filter: contrast(1.015);
    }}
    .decision-reroll  .plate-mat {{ box-shadow: 0 0 0 1px rgba(184,64,26,0.18), 0 30px 50px -40px rgba(21,18,12,0.55); }}
    .decision-reject  .plate-mat {{ box-shadow: 0 0 0 1px rgba(21,18,12,0.55),  0 30px 50px -40px rgba(21,18,12,0.65); }}
    .decision-approve .plate-mat {{ box-shadow: 0 0 0 1px rgba(74,96,69,0.25),  0 30px 50px -40px rgba(21,18,12,0.55); }}

    .plate-caption {{ margin-top: 18px; }}
    .plate-title {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 96, "SOFT" 30, "WONK" 1;
      font-style: italic;
      font-weight: 360;
      font-size: clamp(24px, 2.2vw, 32px);
      line-height: 1.1;
      letter-spacing: -0.012em;
      margin: 0;
      color: var(--ink);
    }}
    .plate-subtitle {{
      margin: 6px 0 0;
      font-family: "Geist Mono", monospace;
      font-size: 11px; letter-spacing: 0.06em;
      color: var(--ink-soft);
    }}
    .plate-subtitle .qa-num {{ color: var(--ink); font-weight: 600; }}
    .plate-subtitle .qa-status {{
      display: inline-block;
      padding: 1px 8px; margin-left: 4px;
      border: 1px solid var(--rule);
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 9px;
    }}
    .qa-pass         {{ color: var(--moss); border-color: rgba(74,96,69,0.5); }}
    .qa-manual_review {{ color: var(--vermilion); border-color: rgba(184,64,26,0.4); }}
    .qa-fail         {{ color: var(--vermilion-deep); border-color: rgba(142,47,18,0.6); background: rgba(184,64,26,0.06); }}
    .qa-unscored     {{ color: var(--mute); }}

    /* Score sparkline */
    .sparkline {{
      margin-top: 16px;
      padding: 14px 16px 8px;
      border: 1px solid var(--rule-soft);
      background: rgba(255,255,255,0.35);
      display: grid; grid-template-columns: repeat(6, 1fr);
      gap: 8px;
    }}
    .sb {{
      display: grid;
      grid-template-rows: 64px auto auto;
      gap: 4px;
      justify-items: center;
      align-items: end;
    }}
    .sb-bar {{
      width: 100%;
      background: linear-gradient(180deg, var(--ink) 0%, var(--ink-soft) 100%);
      align-self: end;
      transition: height .9s cubic-bezier(.2,.7,.3,1);
    }}
    .decision-reroll  .sb-bar {{ background: linear-gradient(180deg, var(--vermilion) 0%, var(--vermilion-deep) 100%); }}
    .decision-reject  .sb-bar {{ background: linear-gradient(180deg, var(--ink) 0%, #2a2418 100%); }}
    .decision-approve .sb-bar {{ background: linear-gradient(180deg, var(--moss) 0%, #2f4029 100%); }}
    .sb-lbl {{
      font-family: "Geist Mono", monospace;
      font-size: 9px; letter-spacing: 0.16em;
      color: var(--mute);
    }}
    .sb-num {{
      font-family: "Geist Mono", monospace;
      font-size: 11px; color: var(--ink);
    }}

    .plate-body {{ margin-top: 18px; }}
    .plate-meta {{ margin: 0; display: grid; gap: 8px; }}
    .plate-meta > div {{
      display: grid;
      grid-template-columns: 88px 1fr;
      gap: 16px;
      padding-bottom: 8px;
      border-bottom: 1px dashed var(--rule-soft);
    }}
    .plate-meta > div:last-child {{ border-bottom: 0; padding-bottom: 0; }}
    .plate-meta dt {{
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
      color: var(--mute);
      align-self: center;
    }}
    .plate-meta dd {{ margin: 0; font-size: 13px; color: var(--ink); }}

    .plate-reasons, .plate-exports {{ margin-top: 18px; }}
    .plate-reasons-label, .plate-exports-label {{
      display: block;
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
      color: var(--mute);
      margin-bottom: 8px;
    }}
    .plate-reasons ul {{ margin: 0; padding: 0; list-style: none; }}
    .plate-reasons li {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 24, "SOFT" 30;
      font-style: italic;
      font-weight: 380;
      font-size: 14px;
      line-height: 1.45;
      color: var(--ink-soft);
      padding: 5px 0 5px 22px;
      position: relative;
      border-bottom: 1px dotted var(--rule-soft);
    }}
    .plate-reasons li::before {{
      content: "❡";
      position: absolute; left: 0; top: 5px;
      font-style: normal;
      color: var(--vermilion);
      font-family: "Fraunces", serif;
      font-size: 13px;
    }}
    .plate-reasons li.muted {{ color: var(--mute); }}
    .plate-reasons li.muted::before {{ color: var(--rule); content: "—"; }}
    .plate-reasons li:last-child {{ border-bottom: 0; }}

    .export-links {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .export-link {{
      display: inline-flex; align-items: center;
      gap: 0;
      font-family: "Geist Mono", monospace;
      font-size: 11px; letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--ink);
      text-decoration: none;
      border: 1px solid var(--ink);
      transition: background .2s ease, color .2s ease;
    }}
    .export-link .ch {{ padding: 5px 10px; background: var(--ink); color: var(--paper); }}
    .export-link .rt {{ padding: 5px 10px; }}
    .export-link:hover {{ background: var(--ink); color: var(--paper); }}
    .export-link:hover .ch {{ background: var(--vermilion); }}
    .export-link:hover .rt {{ color: var(--paper); }}

    .hidden {{ display: none !important; }}

    /* ─── Colophon ────────────────────────────────────────────────────────── */
    .colophon {{
      margin-top: 88px;
      padding-top: 36px;
      border-top: 4px double var(--ink);
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 1fr);
      gap: 48px;
    }}
    .colophon h2 {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 96, "SOFT" 0, "WONK" 1;
      font-style: italic;
      font-weight: 340;
      font-size: 30px;
      letter-spacing: -0.01em;
      margin: 0 0 16px;
    }}
    .colophon p {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 14, "SOFT" 50;
      font-size: 14px;
      line-height: 1.6;
      color: var(--ink-soft);
      margin: 0 0 12px;
    }}
    .colophon dl {{ margin: 0; display: grid; gap: 8px; }}
    .colophon dl > div {{
      display: grid; grid-template-columns: 110px 1fr; gap: 16px;
      padding-bottom: 8px;
      border-bottom: 1px dashed var(--rule-soft);
    }}
    .colophon dt {{
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
      color: var(--mute);
    }}
    .colophon dd {{
      margin: 0;
      font-family: "Geist Mono", monospace;
      font-size: 11px;
      color: var(--ink);
      word-break: break-all;
    }}
    .colophon-sig {{
      margin-top: 36px;
      grid-column: 1 / -1;
      display: flex; align-items: center; gap: 16px;
      padding-top: 24px;
      border-top: 1px solid var(--rule);
      font-family: "Geist Mono", monospace;
      font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
      color: var(--mute);
    }}
    .colophon-sig .sig {{
      font-family: "Fraunces", serif;
      font-variation-settings: "opsz" 32, "SOFT" 100, "WONK" 1;
      font-style: italic;
      font-weight: 360;
      font-size: 22px;
      letter-spacing: -0.01em;
      color: var(--ink);
      text-transform: none;
    }}

    /* ─── Responsive ─────────────────────────────────────────────────────── */
    @media (max-width: 1080px) {{
      .masthead {{ grid-template-columns: 1fr; gap: 36px; }}
      .ref-plate {{ grid-template-columns: 1fr; gap: 28px; }}
      .index-bar {{ grid-template-columns: 1fr 1fr; }}
      .plates {{ grid-template-columns: 1fr; gap: 56px; }}
      .colophon {{ grid-template-columns: 1fr; gap: 28px; }}
    }}
    @media (max-width: 640px) {{
      .shell {{ padding: 20px 20px 60px; }}
      .colophon-bar {{ flex-wrap: wrap; gap: 8px 16px; font-size: 10px; }}
      .ledger {{ grid-template-columns: 1fr 1fr; }}
      .ledger-cell:nth-child(2) {{ border-right: 0; }}
      .ledger-cell:nth-child(1), .ledger-cell:nth-child(2) {{ border-bottom: 1px solid var(--rule-soft); }}
      .index-bar {{ grid-template-columns: 1fr; }}
      .verdict-stamp {{ top: 16px; right: 0; transform: rotate(-7deg) scale(.86); }}
      .sparkline {{ padding: 10px 12px; }}
      .sb {{ grid-template-rows: 48px auto auto; }}
    }}
  </style>
</head>
<body>
  <div class="shell" data-bsk-magic-moment="true" data-frontend-marker="generated-review-frontend">
    <div class="grain" aria-hidden="true"></div>

    <!-- Top utility bar -->
    <div class="colophon-bar">
      <span><span class="dot"></span> Brand Shoot Kit</span>
      <span>Dossier № {html.escape(dossier_no)}</span>
      <span class="spacer"></span>
      <span>{html.escape(timestamp_pretty)}</span>
      <span class="pill">{html.escape(primary_badge)}</span>
    </div>

    <!-- Masthead -->
    <header class="masthead">
      <div>
        <div class="masthead-eyebrow">
          <span>Brand Photo Studio</span>
          <span class="rule"></span>
          <span>Folio 01 — Review Proofs</span>
        </div>
        <h1>
          {html.escape(brand)}
          <span class="product">{html.escape(product)}</span>
        </h1>
        {('<a class="masthead-url" href="' + html.escape(product_url) + '">' + html.escape(product_url) + '</a>') if product_url else ""}
        <p class="masthead-status">{html.escape(status_text)}</p>
      </div>

      <aside class="studio-card">
        <div class="studio-card-hd"><span>Studio Index Card</span><span>RUN</span></div>
        <dl>
          <div><dt>Run ID</dt><dd>{html.escape(run_id)}</dd></div>
          <div><dt>Provider</dt><dd>{html.escape(provider)}</dd></div>
          <div><dt>Model</dt><dd>{html.escape(model)}</dd></div>
          <div><dt>Endpoint</dt><dd>{html.escape(endpoint)}</dd></div>
          <div><dt>Captured</dt><dd>{html.escape(timestamp)}</dd></div>
          <div><dt>QA Mix</dt><dd>{html.escape(qa_summary)}</dd></div>
        </dl>
      </aside>

      <div class="verdict-stamp {verdict_class}">
        {verdict_word}
        <span class="verdict-sub">Studio Proof</span>
      </div>
    </header>

    <!-- Ledger row -->
    <section class="ledger" aria-label="Frame ledger">
      <div class="ledger-cell total">
        <span class="label">Frames Captured</span>
        <span class="num">{total:02d}</span>
        <span class="delta">across all channels</span>
      </div>
      <div class="ledger-cell approve">
        <span class="label">Suggest · Approve</span>
        <span class="num">{approve_n:02d}</span>
        <span class="delta">stet — ship as-is</span>
      </div>
      <div class="ledger-cell reroll">
        <span class="label">Suggest · Reroll</span>
        <span class="num">{reroll_n:02d}</span>
        <span class="delta">rework with new pass</span>
      </div>
      <div class="ledger-cell reject">
        <span class="label">Suggest · Reject</span>
        <span class="num">{reject_n:02d}</span>
        <span class="delta">kill, escalate to operator</span>
      </div>
    </section>

    <!-- Reference plate -->
    {ref_block}

    <!-- Index / filter bar -->
    <section class="index-bar" aria-label="Plate filters">
      <div class="index-bar-title">
        Plate Index
        <small>{total:02d} frames · filter the dossier</small>
      </div>
      <div>
        <label for="filter-decision">Decision</label>
        <select id="filter-decision">
          <option value="">All</option>
          <option value="approve">Approve · stet</option>
          <option value="reroll">Reroll · rework</option>
          <option value="reject">Reject · kill</option>
        </select>
      </div>
      <div>
        <label for="filter-qa">QA status</label>
        <select id="filter-qa">
          <option value="">All</option>
          <option value="pass">pass</option>
          <option value="manual_review">manual review</option>
          <option value="fail">fail</option>
          <option value="unscored">unscored</option>
        </select>
      </div>
      <div>
        <label for="filter-channel">Channel</label>
        <input id="filter-channel" type="text" placeholder="pdp, social, amazon…" />
      </div>
      <div>
        <label for="filter-name">Search shot</label>
        <input id="filter-name" type="text" placeholder="shot name or asset id" />
      </div>
    </section>

    <!-- Plate gallery -->
    <section id="generated-gallery" class="plates" data-gallery="generated-images" data-card-count="{total}">
      {cards}
    </section>

    <!-- Colophon -->
    <footer class="colophon">
      <div>
        <h2>Colophon &amp; Provenance</h2>
        <p>Every frame in this dossier records its complete provenance — the model that drew it,
        the reference image that anchored it, the dimensions it was rendered at, and the SHA-256
        hash of the pixel output. Nothing here is a screenshot.</p>
        <p class="muted">Brand Shoot Kit composes deterministic strategy artifacts (scout, preserve,
        gap audit, shot plan, prompts) and feeds them into a generation, QA, reroll, and export
        pipeline. This page is the magic-moment review surface — the deliverable.</p>
      </div>
      <div>
        <dl>
          <div><dt>Run ID</dt><dd>{html.escape(run_id)}</dd></div>
          <div><dt>Generated</dt><dd>{html.escape(timestamp)}</dd></div>
          <div><dt>Provider</dt><dd>{html.escape(provider)} · {html.escape(model)}</dd></div>
          <div><dt>Endpoint</dt><dd>{html.escape(endpoint)}</dd></div>
          <div><dt>{html.escape(_scout_scraper_label(packet))}</dt><dd>scout source</dd></div>
          <div><dt>Reference</dt><dd>{html.escape(reference_path)}</dd></div>
        </dl>
      </div>
      <div>
        <dl>
          <div><dt>Packet</dt><dd>{packet_rel}</dd></div>
          <div><dt>Magic Index</dt><dd><a href="{magic_link}">{magic_link}</a></dd></div>
          <div><dt>Contact Sheet</dt><dd><a href="{contact_link}">{contact_link}</a></dd></div>
          <div><dt>Export Manifest</dt><dd>{html.escape(str(export_manifest_path))}</dd></div>
          <div><dt>Command Log</dt><dd>{html.escape(str(run_log))} ({'present' if run_log.exists() else 'missing'})</dd></div>
        </dl>
      </div>
      <div class="colophon-sig">
        <span class="sig">Brand Shoot Kit</span>
        <span>set in Fraunces &amp; Geist Mono</span>
        <span>—</span>
        <span>printed on cream № {html.escape(dossier_no)}</span>
      </div>
    </footer>
  </div>

  <script>
    (function () {{
      // Stagger reveal — set --i index per plate so CSS animation-delay scales
      const plates = Array.from(document.querySelectorAll('.generated-image-card'));
      plates.forEach((p, i) => p.style.setProperty('--i', i));

      const decision = document.getElementById('filter-decision');
      const qa       = document.getElementById('filter-qa');
      const channel  = document.getElementById('filter-channel');
      const name     = document.getElementById('filter-name');

      function applyFilters() {{
        const d = (decision.value || '').toLowerCase().trim();
        const q = (qa.value || '').toLowerCase().trim();
        const c = (channel.value || '').toLowerCase().trim();
        const n = (name.value || '').toLowerCase().trim();

        plates.forEach((card) => {{
          const passDecision = !d || card.dataset.decision === d;
          const passQa       = !q || card.dataset.qa === q;
          const passChannel  = !c || (card.dataset.channels || '').includes(c);
          const titleText    = (card.querySelector('.plate-title')?.textContent || '').toLowerCase();
          const subText      = (card.querySelector('.plate-subtitle')?.textContent || '').toLowerCase();
          const text = (card.dataset.name || '') + ' ' + titleText + ' ' + subText;
          const passName     = !n || text.includes(n);
          card.classList.toggle('hidden', !(passDecision && passQa && passChannel && passName));
        }});
      }}

      [decision, qa, channel, name].forEach((el) => el && el.addEventListener('input', applyFilters));
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
                "use_case": entry.get("use_case") or "",
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
