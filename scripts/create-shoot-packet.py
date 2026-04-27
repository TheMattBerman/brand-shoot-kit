#!/usr/bin/env python3
import argparse
import json
import os
from datetime import date
from typing import Dict, List

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

CRITERIA = [
    ("Product accuracy", 30),
    ("Commerce usefulness", 20),
    ("Brand fit", 15),
    ("Scene realism", 15),
    ("Visual clarity", 10),
    ("AI artifact risk", 10),
]

CATEGORY_SHOT_TEMPLATES = {
    "skincare": [
        ("Front label hero", "PDP", "1:1", "PDP", "High"),
        ("Dropper angle detail", "PDP", "4:5", "PDP", "High"),
        ("Ingredient texture smear", "Lifestyle", "1:1", "PDP/Social", "High"),
        ("Sink routine placement", "Lifestyle", "4:5", "PDP/Email", "High"),
        ("Morning hand-held scale", "Model", "4:5", "PDP/Social", "High"),
        ("Shelf trio context", "Lifestyle", "4:5", "Social", "Medium"),
        ("Body crop application", "Model", "9:16", "Social", "Medium"),
        ("Email routine hero", "Email", "16:9", "Email", "High"),
        ("Seasonal gift bundle", "Seasonal", "4:5", "Email/Social", "Low"),
        ("Marketplace white-ground", "Marketplace", "1:1", "Amazon", "High"),
        ("Social benefit square", "Social", "1:1", "Instagram", "Medium"),
        ("Story routine vertical", "Social", "9:16", "Instagram Story", "Medium"),
    ],
    "coffee": [
        ("Front pack hero", "PDP", "1:1", "PDP", "High"),
        ("Roast label angle", "PDP", "4:5", "PDP", "High"),
        ("Beans + bag texture", "Lifestyle", "1:1", "PDP/Social", "High"),
        ("Pour-over counter scene", "Lifestyle", "4:5", "PDP/Email", "High"),
        ("Hand scoop scale", "Model", "4:5", "PDP/Social", "High"),
        ("Pantry shelf context", "Lifestyle", "4:5", "Social", "Medium"),
        ("Steam mug body crop", "Model", "9:16", "Social", "Medium"),
        ("Email morning hero", "Email", "16:9", "Email", "High"),
        ("Holiday gifting stack", "Seasonal", "4:5", "Email/Social", "Low"),
        ("Marketplace white-ground", "Marketplace", "1:1", "Amazon", "High"),
        ("Social brew square", "Social", "1:1", "Instagram", "Medium"),
        ("Story brew vertical", "Social", "9:16", "Instagram Story", "Medium"),
    ],
    "supplement": [
        ("Front tub hero", "PDP", "1:1", "PDP", "High"),
        ("Supplement-facts angle", "PDP", "4:5", "PDP", "High"),
        ("Powder + scoop texture", "Lifestyle", "1:1", "PDP/Social", "High"),
        ("Morning counter routine", "Lifestyle", "4:5", "PDP/Email", "High"),
        ("Hand-held shake prep", "Model", "4:5", "PDP/Social", "High"),
        ("Kitchen shelf context", "Lifestyle", "4:5", "Social", "Medium"),
        ("Body crop mixing action", "Model", "9:16", "Social", "Medium"),
        ("Email routine hero", "Email", "16:9", "Email", "High"),
        ("Seasonal wellness gifting", "Seasonal", "4:5", "Email/Social", "Low"),
        ("Marketplace white-ground", "Marketplace", "1:1", "Amazon", "High"),
        ("Social trust square", "Social", "1:1", "Instagram", "Medium"),
        ("Story prep vertical", "Social", "9:16", "Instagram Story", "Medium"),
    ],
    "home-goods": [
        ("Front jar hero", "PDP", "1:1", "PDP", "High"),
        ("Label + wax angle", "PDP", "4:5", "PDP", "High"),
        ("Surface texture detail", "Lifestyle", "1:1", "PDP/Social", "High"),
        ("Styled shelf vignette", "Lifestyle", "4:5", "PDP/Email", "High"),
        ("Hand-lit scale context", "Model", "4:5", "PDP/Social", "Medium"),
        ("Bedside table context", "Lifestyle", "4:5", "Social", "Medium"),
        ("Body crop ambiance", "Model", "9:16", "Social", "Low"),
        ("Email mood hero", "Email", "16:9", "Email", "High"),
        ("Seasonal gifting pair", "Seasonal", "4:5", "Email/Social", "Medium"),
        ("Marketplace white-ground", "Marketplace", "1:1", "Amazon", "High"),
        ("Social decor square", "Social", "1:1", "Instagram", "Medium"),
        ("Story ambiance vertical", "Social", "9:16", "Instagram Story", "Medium"),
    ],
    "generic": [
        ("Front hero clean", "PDP", "1:1", "PDP", "High"),
        ("Angle detail", "PDP", "4:5", "PDP", "High"),
        ("Scale-in-hand", "Model", "4:5", "PDP/Social", "High"),
        ("Lifestyle context", "Lifestyle", "4:5", "PDP/Email", "High"),
        ("Texture close-up", "Lifestyle", "1:1", "PDP", "Medium"),
        ("Shelf context", "Lifestyle", "4:5", "Social", "Medium"),
        ("Body crop application", "Model", "9:16", "Social", "Medium"),
        ("Email hero", "Email", "16:9", "Email", "High"),
        ("Seasonal gifting", "Seasonal", "4:5", "Email/Social", "Low"),
        ("Marketplace white", "Marketplace", "1:1", "Amazon", "High"),
        ("Social square", "Social", "1:1", "Instagram", "Medium"),
        ("Story vertical", "Social", "9:16", "Instagram Story", "Medium"),
    ],
}

CATEGORY_SCENE_HINTS = {
    "skincare": "Use clean vanity, stone, glass, folded towels, and subtle botanical accents. Avoid heavy makeup mood.",
    "coffee": "Use wood or stone counters, brewing tools, beans, steam, and warm morning light. Avoid cafe branding noise.",
    "supplement": "Use kitchen or desk routine context with shaker, water, or scoop cues. Keep claims presentation credible.",
    "home-goods": "Use interior decor context with soft textile, wood, and ambient practical lighting. Avoid clutter.",
    "generic": "Use ecommerce-safe set design with believable props and clear product dominance.",
}


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
    os.makedirs(os.path.join(root, "assets", "generated"), exist_ok=True)
    os.makedirs(os.path.join(root, "assets", "exports"), exist_ok=True)
    os.makedirs(os.path.join(root, "memory"), exist_ok=True)


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n")


def infer_category(cfg: dict) -> str:
    corpus = " ".join(
        [
            str(cfg.get("product_type", "")),
            str(cfg.get("product", "")),
            str(cfg.get("product_url", "")),
            str(cfg.get("source_snapshot", {}).get("meta_description", "")),
        ]
    ).lower()

    if any(k in corpus for k in ["serum", "skincare", "moistur", "cleanser", "dropper", "cream"]):
        return "skincare"
    if any(k in corpus for k in ["coffee", "espresso", "beans", "brew", "roast"]):
        return "coffee"
    if any(k in corpus for k in ["supplement", "greens", "protein", "powder", "capsule", "vitamin"]):
        return "supplement"
    if any(k in corpus for k in ["candle", "home", "decor", "jar", "sofa", "linen", "room spray"]):
        return "home-goods"
    return "generic"


def keyword_evidence(cfg: dict) -> List[str]:
    parts = [
        str(cfg.get("source_snapshot", {}).get("meta_description", "")),
        str(cfg.get("strategy_rationale", "")),
        " ".join(str(x) for x in cfg.get("must_preserve", [])),
        " ".join(str(x) for x in cfg.get("distortion_risks", [])),
    ]
    text = " ".join(parts).lower()
    keywords = []
    for word in [
        "hyaluronic",
        "niacinamide",
        "vitamin",
        "caffeine",
        "roast",
        "single origin",
        "soy",
        "amber",
        "scoop",
        "powder",
        "dropper",
        "glass",
        "label",
    ]:
        if word in text:
            keywords.append(word)
    return keywords[:4]


def default_shots_for_category(category: str) -> List[Dict[str, str]]:
    rows = CATEGORY_SHOT_TEMPLATES.get(category, CATEGORY_SHOT_TEMPLATES["generic"])
    return [
        {
            "name": name,
            "category": cat,
            "ratio": ratio,
            "channel": channel,
            "priority": priority,
        }
        for name, cat, ratio, channel, priority in rows
    ]


def compose_prompt(
    shot: Dict[str, str],
    product: str,
    brand: str,
    tone: str,
    scene_hint: str,
    must_preserve: List[str],
    never_change: List[str],
    distortion_risks: List[str],
    evidence_tokens: List[str],
) -> str:
    evidence_text = ", ".join(evidence_tokens) if evidence_tokens else "none extracted"
    preserve_text = ", ".join(must_preserve[:4]) if must_preserve else "package geometry and label hierarchy"
    never_text = ", ".join(never_change[:3]) if never_change else "brand name spelling and required claims"
    risk_text = ", ".join(distortion_risks[:3]) if distortion_risks else "label drift and geometry distortion"

    return (
        f"Create a {shot.get('ratio')} ecommerce image for {product} ({brand}) optimized for {shot.get('channel')}. "
        f"Shot intent: {shot.get('name')}. Product should occupy 32-48% of frame with label-facing readability priority. "
        f"Brand tone: {tone}. Scene direction: {scene_hint} "
        f"Evidence anchors from source: {evidence_text}. "
        f"Must preserve exactly: {preserve_text}. Never change: {never_text}. "
        f"Watch distortion risks: {risk_text}. Keep props supportive, never dominant."
    )


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

    category = infer_category(cfg)
    evidence_tokens = keyword_evidence(cfg)
    source_snapshot = cfg.get("source_snapshot", {}) or {}

    brand_analysis = f"""# Brand Analysis\n\n- Brand: {brand}\n- Product: {product}\n- URL: {cfg.get('product_url', 'not provided')}\n- Price tier: {cfg.get('price_tier', 'unknown')}\n- Audience: {cfg.get('audience', 'unknown')}\n- Tone: {cfg.get('tone', 'unknown')}\n- Palette: {', '.join(cfg.get('palette', [])) or 'unknown'}\n- Inferred product category: {category}\n\n## Product Preservation Brief\n- Product type: {cfg.get('product_type', 'unknown')}\n- Must preserve: {', '.join(cfg.get('must_preserve', [])) or 'exact pack shape, label position, logo'}\n- Can vary: {', '.join(cfg.get('can_vary', [])) or 'camera angle, scene context, background depth'}\n- Never change: {', '.join(cfg.get('never_change', [])) or 'label claims, brand name spelling, package geometry'}\n- Distortion risks: {', '.join(cfg.get('distortion_risks', [])) or 'text warping, cap geometry drift, scale mismatch'}\n- Accuracy confidence: {cfg.get('accuracy_confidence', 'medium')}\n\n## Source Evidence Snapshot\n- Source title: {source_snapshot.get('title', 'n/a')}\n- Source H1: {', '.join(source_snapshot.get('h1', [])[:2]) if isinstance(source_snapshot.get('h1'), list) else 'n/a'}\n- Source summary: {source_snapshot.get('meta_description', 'n/a')}\n- Evidence keywords used in prompts: {', '.join(evidence_tokens) or 'none'}\n"""

    visual_gaps = "# Visual Gap Audit\n\n| Asset Type | Status | Notes | Priority |\n|---|---|---|---|\n"
    for row in cfg.get("visual_gaps", []):
        visual_gaps += f"| {row.get('asset','Unknown')} | {row.get('status','Missing')} | {row.get('notes','')} | {row.get('priority','Medium')} |\n"
    if not cfg.get("visual_gaps"):
        visual_gaps += "| Model in-use | Missing | No human scale context | High |\n"
        visual_gaps += "| Texture proof | Unknown | Needs material/formula detail image | Medium |\n"

    strategy = f"""# Shoot Strategy\n\n## Candidate Directions\n1. Conversion-safe commerce precision\n2. Contextual lifestyle trust-build\n3. Social-native narrative moments\n\n## Recommended Direction\n{cfg.get('recommended_direction', 'Contextual lifestyle trust-build with commerce-safe fallbacks')}\n\n## Why\n{cfg.get('strategy_rationale', 'Prioritize conversion clarity first, then emotional context where it does not compromise product truth.')}\n\n## Category Lens\n- Category: {category}\n- Category scene guidance: {CATEGORY_SCENE_HINTS.get(category, CATEGORY_SCENE_HINTS['generic'])}\n"""

    shots = cfg.get("shots", [])
    if not shots:
        shots = default_shots_for_category(category)

    shot_list = "# Shot List\n\n| # | Shot Name | Category | Ratio | Channel | Priority |\n|---:|---|---|---|---|---|\n"
    prompts = "# Generation Prompts\n\n"
    export_map = "# Export Map\n\n| Shot | Best Use | Why |\n|---|---|---|\n"

    scene_hint = CATEGORY_SCENE_HINTS.get(category, CATEGORY_SCENE_HINTS["generic"])
    must_preserve = [str(x) for x in cfg.get("must_preserve", [])]
    never_change = [str(x) for x in cfg.get("never_change", [])]
    distortion_risks = [str(x) for x in cfg.get("distortion_risks", [])]

    for idx, s in enumerate(shots, 1):
        shot_list += f"| {idx} | {s.get('name')} | {s.get('category')} | {s.get('ratio')} | {s.get('channel')} | {s.get('priority')} |\n"

        prompt_text = compose_prompt(
            s,
            product,
            brand,
            cfg.get("tone", "balanced ecommerce"),
            scene_hint,
            must_preserve,
            never_change,
            distortion_risks,
            evidence_tokens,
        )

        prompts += (
            f"## Shot {idx:02d} - {s.get('name')}\n\n"
            f"**Use case:** {s.get('category')}\n"
            f"**Aspect ratio:** {s.get('ratio')}\n\n"
            "**Prompt:**\n"
            f"{prompt_text}\n\n"
            "**Negative constraints:**\n"
            f"- no altered logo or label text\n"
            f"- no fake ingredient/claim badges\n"
            f"- no malformed hands or impossible anatomy\n"
            f"- no product count mismatch for intended SKU\n"
            f"- no prop occlusion hiding the primary label\n\n"
            "**Reroll if failed:**\n"
            "If label legibility, pack geometry, or product count fails, reroll with flatter camera angle, cleaner background, and tighter product framing.\n\n"
        )

        export_map += (
            f"| {s.get('name')} | {s.get('channel')} | "
            f"{s.get('category')} shot for {category} category goals with preservation-first framing. |\n"
        )

    qa_rows = "\n".join([f"| {name} | {weight} | TBD | |" for name, weight in CRITERIA])
    qa = f"""# QA Report\n\n## Run Status\n- Generation: Not Run (planning mode by default)\n- Automated QA: Not Run\n\n## Rubric\n| Criterion | Weight | Score | Notes |\n|---|---:|---:|---|\n{qa_rows}\n\n## Automatic Rejection Triggers\n- label text changed\n- product geometry changed\n- unreadable key text\n- malformed hand interacting with product\n- fake claims/certification\n- product too small for commerce utility\n"""

    files = {
        "00-brand-analysis.md": brand_analysis,
        "01-visual-gap-audit.md": visual_gaps,
        "02-shoot-strategy.md": strategy,
        "03-shot-list.md": shot_list,
        "04-generation-prompts.md": (
            prompts
            + "## Manual Generation Runbook\n"
            + "1. Generate priority High shots first and keep all manifests.\n"
            + "2. Run ./scripts/qa-images.py after each generation batch.\n"
            + "3. Only package assets that pass QA or are manually approved.\n"
        ),
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
