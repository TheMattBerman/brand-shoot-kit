#!/usr/bin/env python3
import argparse
import json
import os
from datetime import date

REQUIRED_DOCS = [
    "00-brand-analysis.md",
    "01-visual-gap-audit.md",
    "02-shoot-strategy.md",
    "03-shot-list.md",
    "04-generation-prompts.md",
    "05-qa-report.md",
    "06-export-map.md",
]

ASSET_DIRS = ["pdp", "lifestyle", "model", "seasonal", "social", "email", "marketplace"]


def slug(v: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in v)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_packet_dirs(root: str) -> None:
    os.makedirs(root, exist_ok=True)
    os.makedirs(os.path.join(root, "assets"), exist_ok=True)
    for d in ASSET_DIRS:
        os.makedirs(os.path.join(root, "assets", d), exist_ok=True)
    os.makedirs(os.path.join(root, "memory"), exist_ok=True)


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Brand Shoot Kit planning packet from JSON config")
    parser.add_argument("--config", required=True, help="Path to packet config JSON")
    parser.add_argument("--out", help="Output directory (default: ./output/<brand>/<product>/<today>)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    brand = cfg.get("brand", "Unknown Brand")
    product = cfg.get("product", "Unknown Product")
    today = date.today().isoformat()

    out_dir = args.out or os.path.join("output", slug(brand), slug(product), today)
    ensure_packet_dirs(out_dir)

    brand_analysis = f"""# Brand Analysis\n\n- Brand: {brand}\n- Product: {product}\n- URL: {cfg.get('product_url', 'not provided')}\n- Price tier: {cfg.get('price_tier', 'unknown')}\n- Audience: {cfg.get('audience', 'unknown')}\n- Tone: {cfg.get('tone', 'unknown')}\n- Palette: {', '.join(cfg.get('palette', [])) or 'unknown'}\n\n## Product Preservation Brief\n- Product type: {cfg.get('product_type', 'unknown')}\n- Must preserve: {', '.join(cfg.get('must_preserve', [])) or 'exact pack shape, label position, logo'}\n- Can vary: {', '.join(cfg.get('can_vary', [])) or 'camera angle, scene context, background depth'}\n- Never change: {', '.join(cfg.get('never_change', [])) or 'label claims, brand name spelling, package geometry'}\n- Distortion risks: {', '.join(cfg.get('distortion_risks', [])) or 'text warping, cap geometry drift, scale mismatch'}\n- Accuracy confidence: {cfg.get('accuracy_confidence', 'medium')}\n"""

    visual_gaps = "# Visual Gap Audit\n\n| Asset Type | Status | Notes | Priority |\n|---|---|---|---|\n"
    for row in cfg.get("visual_gaps", []):
        visual_gaps += f"| {row.get('asset','Unknown')} | {row.get('status','Missing')} | {row.get('notes','')} | {row.get('priority','Medium')} |\n"
    if not cfg.get("visual_gaps"):
        visual_gaps += "| Model in-use | Missing | No human scale context | High |\n"

    strategy = f"""# Shoot Strategy\n\n## Candidate Directions\n1. Clean Commerce\n2. Editorial Lifestyle\n3. Social Native\n\n## Recommended Direction\n{cfg.get('recommended_direction', 'Editorial Lifestyle with commerce-safe exports')}\n\n## Why\n{cfg.get('strategy_rationale', 'Improves conversion clarity while preserving brand tone and product trust.')}\n"""

    shots = cfg.get("shots", [])
    if not shots:
        shots = [
            {"name": "Front hero clean", "category": "PDP", "ratio": "1:1", "channel": "PDP", "priority": "High"},
            {"name": "Angle detail", "category": "PDP", "ratio": "4:5", "channel": "PDP", "priority": "High"},
            {"name": "Scale-in-hand", "category": "Model", "ratio": "4:5", "channel": "PDP/Social", "priority": "High"},
            {"name": "Bathroom routine", "category": "Lifestyle", "ratio": "4:5", "channel": "PDP/Email", "priority": "High"},
            {"name": "Texture close-up", "category": "Lifestyle", "ratio": "1:1", "channel": "PDP", "priority": "Medium"},
            {"name": "Shelf context", "category": "Lifestyle", "ratio": "4:5", "channel": "Social", "priority": "Medium"},
            {"name": "Body crop application", "category": "Model", "ratio": "9:16", "channel": "Social", "priority": "Medium"},
            {"name": "Email hero", "category": "Email", "ratio": "16:9", "channel": "Email", "priority": "High"},
            {"name": "Seasonal gifting", "category": "Seasonal", "ratio": "4:5", "channel": "Email/Social", "priority": "Low"},
            {"name": "Marketplace white", "category": "Marketplace", "ratio": "1:1", "channel": "Amazon", "priority": "High"},
            {"name": "Social square", "category": "Social", "ratio": "1:1", "channel": "Instagram", "priority": "Medium"},
            {"name": "Story vertical", "category": "Social", "ratio": "9:16", "channel": "Instagram Story", "priority": "Medium"},
        ]

    shot_list = "# Shot List\n\n| # | Shot Name | Category | Ratio | Channel | Priority |\n|---:|---|---|---|---|---|\n"
    prompts = "# Generation Prompts\n\n"
    export_map = "# Export Map\n\n| Shot | Best Use | Why |\n|---|---|---|\n"
    for idx, s in enumerate(shots, 1):
        shot_list += f"| {idx} | {s.get('name')} | {s.get('category')} | {s.get('ratio')} | {s.get('channel')} | {s.get('priority')} |\n"
        prompts += (
            f"## Shot {idx:02d} - {s.get('name')}\n\n"
            f"**Use case:** {s.get('category')}\n"
            f"**Aspect ratio:** {s.get('ratio')}\n\n"
            "**Prompt:**\n"
            f"Create a {s.get('ratio')} ecommerce product image for {product}. Keep package geometry, brand name, and label text unchanged. "
            f"Scene intent: {s.get('name')}. Match {brand} tone ({cfg.get('tone','balanced')}). Product is the visual anchor.\n\n"
            "**Negative constraints:**\n"
            "- no altered logo or label text\n"
            "- no extra products unless shot requires bundle\n"
            "- no malformed hands\n"
            "- no fake badges/certifications\n\n"
            "**Reroll if failed:**\n"
            "If label or product geometry drifts, reroll with camera closer, flatter angle, and reduced background complexity.\n\n"
        )
        export_map += f"| {s.get('name')} | {s.get('channel')} | Supports {s.get('category')} objective with clear product context. |\n"

    qa = """# QA Report\n\n## Run Status\n- Generation: Not Run (planning mode by default)\n\n## Rubric\n| Criterion | Weight | Score | Notes |\n|---|---:|---:|---|\n| Product accuracy | 30 | TBD | |\n| Commerce usefulness | 20 | TBD | |\n| Brand fit | 15 | TBD | |\n| Scene realism | 15 | TBD | |\n| Visual clarity | 10 | TBD | |\n| AI artifact risk | 10 | TBD | |\n\n## Automatic Rejection Triggers\n- label text changed\n- product geometry changed\n- unreadable key text\n- malformed hand interacting with product\n- fake claims/certification\n- product too small for commerce utility\n"""

    files = {
        "00-brand-analysis.md": brand_analysis,
        "01-visual-gap-audit.md": visual_gaps,
        "02-shoot-strategy.md": strategy,
        "03-shot-list.md": shot_list,
        "04-generation-prompts.md": prompts + "## Manual Generation Runbook\n1. Select top priority shots first.\n2. Generate 2-4 variants per shot.\n3. Apply QA rejection triggers before export.\n",
        "05-qa-report.md": qa,
        "06-export-map.md": export_map,
        "memory/visual-profile.md": "# Visual Profile\n\nApproved worlds, rejected worlds, and recurring style rules.\n",
        "memory/product-shot-memory.md": "# Product Shot Memory\n\nPrompt fragments that passed/failed and fidelity constraints.\n",
        "memory/assets.md": "# Assets Log\n\nTrack approved files and channel placements.\n",
    }

    for rel, content in files.items():
        write_file(os.path.join(out_dir, rel), content)

    missing = [f for f in REQUIRED_DOCS if not os.path.isfile(os.path.join(out_dir, f))]
    if missing:
        raise RuntimeError(f"Packet incomplete, missing: {missing}")

    print(out_dir)


if __name__ == "__main__":
    main()
