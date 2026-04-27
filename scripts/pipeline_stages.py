#!/usr/bin/env python3
"""Stage artifact builders and markdown renderers for Brand Shoot Kit."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

from packet_utils import dump_json, slug

ASSET_DIRS = ["pdp", "lifestyle", "model", "seasonal", "social", "email", "marketplace"]

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


def clean_text(value: str) -> str:
    return " ".join((value or "").replace("|", " ").split()).strip()


def infer_brand_and_product(scout: Dict[str, Any], fallback_url: str) -> Tuple[str, str]:
    structured_brand = clean_text(str(scout.get("brand_name", "")))
    structured_product = clean_text(str(scout.get("product_name", "")))
    if structured_brand and structured_product:
        return structured_brand, structured_product

    title = clean_text(str(scout.get("og_title") or scout.get("title") or ""))
    h1 = ""
    h1_list = scout.get("h1") or []
    if isinstance(h1_list, list) and h1_list:
        h1 = clean_text(str(h1_list[0]))

    brand = ""
    product = ""

    if title:
        for sep in ["|", "-", "::"]:
            if sep in title:
                parts = [p.strip() for p in title.split(sep) if p.strip()]
                if len(parts) >= 2:
                    product = parts[0]
                    brand = parts[-1]
                    break
        if not product:
            product = title

    if h1 and len(h1) >= 3:
        if not product:
            product = h1
        elif len(h1) > len(product):
            product = h1

    if not brand:
        url = fallback_url or str(scout.get("url", ""))
        host = url.split("//")[-1].split("/")[0].split(":")[0]
        brand = host.replace("www.", "").split(".")[0].replace("-", " ").title() if host else "Unknown Brand"

    return brand or "Unknown Brand", product or "Unknown Product"


def top_images(scout: Dict[str, Any], limit: int = 5) -> List[str]:
    images = scout.get("image_urls") or []
    if not isinstance(images, list):
        return []
    out: List[str] = []
    seen = set()
    for item in images:
        url = str(item).strip()
        if not url or url in seen:
            continue
        out.append(url)
        seen.add(url)
        if len(out) >= limit:
            break
    return out


def infer_product_type(scout: Dict[str, Any], product: str) -> str:
    corpus = " ".join(
        [
            clean_text(str(scout.get("title", ""))),
            clean_text(str(scout.get("meta_description", ""))),
            clean_text(product),
            clean_text(str(scout.get("url", ""))),
        ]
    ).lower()

    if any(k in corpus for k in ["serum", "cleanser", "moistur", "dropper", "skincare"]):
        return "skincare bottle"
    if any(k in corpus for k in ["coffee", "beans", "brew", "roast"]):
        return "sealed coffee bag"
    if any(k in corpus for k in ["greens", "supplement", "powder", "vitamin"]):
        return "supplement tub"
    if any(k in corpus for k in ["candle", "jar", "wax", "home fragrance"]):
        return "glass jar candle"
    return "packaged consumer product"


def infer_category(scout: Dict[str, Any], product_type: str, product: str) -> str:
    corpus = " ".join(
        [
            str(product_type),
            str(product),
            str(scout.get("url", "")),
            str(scout.get("meta_description", "")),
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


def infer_audience(description: str) -> str:
    text = description.lower()
    if any(k in text for k in ["daily", "routine", "everyday"]):
        return "daily routine shoppers"
    if any(k in text for k in ["gift", "gifting"]):
        return "gift-oriented shoppers"
    if any(k in text for k in ["professional", "athlete", "health"]):
        return "performance and wellness buyers"
    return "ecommerce shoppers"


def infer_tone(description: str) -> str:
    text = description.lower()
    if any(k in text for k in ["clinical", "dermat", "ingredient"]):
        return "quiet clinical"
    if any(k in text for k in ["craft", "artisan", "single origin"]):
        return "warm craft premium"
    if any(k in text for k in ["minimal", "calm", "home"]):
        return "calm editorial"
    if any(k in text for k in ["energy", "active", "performance"]):
        return "credible and energetic"
    return "brand-consistent ecommerce"


def infer_preservation_rules(product_type: str) -> Dict[str, List[str]]:
    p = product_type.lower()
    if "skincare" in p:
        return {
            "must_preserve": ["bottle silhouette", "cap geometry", "front label hierarchy"],
            "can_vary": ["set styling", "camera angle", "background depth"],
            "never_change": ["brand name", "ingredient claims", "product count"],
            "distortion_risks": ["small label text drift", "cap deformation", "glass glare"],
        }
    if "coffee" in p:
        return {
            "must_preserve": ["bag silhouette", "origin/roast callouts", "brand lockup"],
            "can_vary": ["brew props", "counter surface", "lighting warmth"],
            "never_change": ["origin text", "net weight", "brand name"],
            "distortion_risks": ["bag fold distortion", "small text drift", "scale mismatch"],
        }
    if "supplement" in p:
        return {
            "must_preserve": ["tub silhouette", "front claims", "supplement facts label"],
            "can_vary": ["props", "camera angle", "scene context"],
            "never_change": ["nutrition claims", "servings text", "brand name"],
            "distortion_risks": ["claim text drift", "scoop scale mismatch", "label warp"],
        }
    if "candle" in p:
        return {
            "must_preserve": ["jar proportions", "glass tone", "label typography"],
            "can_vary": ["room styling", "props", "angle"],
            "never_change": ["scent name", "brand name", "burn-time claims"],
            "distortion_risks": ["reflection artifacts", "label warp", "wick geometry errors"],
        }
    return {
        "must_preserve": ["package geometry", "brand mark", "primary label text"],
        "can_vary": ["camera angle", "lighting direction", "set and props"],
        "never_change": ["brand name spelling", "required claims and warnings", "product count"],
        "distortion_risks": ["label text drift", "shape distortion", "scale mismatch"],
    }


def keyword_evidence(scout: Dict[str, Any], preservation: Dict[str, Any], strategy_rationale: str) -> List[str]:
    parts = [
        str(scout.get("meta_description", "")),
        str(strategy_rationale),
        " ".join(str(x) for x in preservation.get("must_preserve", [])),
        " ".join(str(x) for x in preservation.get("distortion_risks", [])),
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


def stage_preservation(
    scout: Dict[str, Any],
    *,
    product: str,
    explicit_product_type: str | None = None,
    explicit_tone: str | None = None,
    explicit_audience: str | None = None,
) -> Dict[str, Any]:
    product_type = explicit_product_type or str(scout.get("product_type") or infer_product_type(scout, product))
    description = clean_text(str(scout.get("meta_description") or scout.get("og_description") or ""))
    field_conf = scout.get("field_confidence") or {}
    confidence = "medium-high" if description and len(description) > 120 else "medium"
    if isinstance(field_conf, dict):
        low_fields = [k for k in ["claims_benefits", "ingredients_materials_specs", "price"] if float(field_conf.get(k, 0.0)) < 0.5]
        if low_fields:
            confidence = "low"
        elif float(field_conf.get("visible_packaging_text_candidates", 0.0)) < 0.6:
            confidence = "medium-low"
    rules = infer_preservation_rules(product_type)
    can_vary = rules["can_vary"]
    if confidence in {"low", "medium-low"}:
        can_vary = ["camera angle (safe)", "background depth (minimal)", "neutral scene context"]

    return {
        "product_type": product_type,
        "must_preserve": rules["must_preserve"],
        "can_vary": can_vary,
        "never_change": rules["never_change"],
        "distortion_risks": rules["distortion_risks"],
        "accuracy_confidence": confidence,
        "audience": explicit_audience or infer_audience(description),
        "tone": explicit_tone or infer_tone(description),
    }


def stage_visual_gaps(scout: Dict[str, Any], preservation: Dict[str, Any]) -> Dict[str, Any]:
    category = infer_category(scout, str(preservation.get("product_type", "")), str(scout.get("title", "")))
    rows = [
        {
            "asset": "PDP hero",
            "status": "Unknown",
            "notes": "Review current hero quality from source page",
            "priority": "High",
        },
        {
            "asset": "Human scale/in-use",
            "status": "Unknown",
            "notes": "Confirm if human context exists",
            "priority": "High",
        },
        {
            "asset": "Texture/detail proof",
            "status": "Unknown",
            "notes": "Need feature clarity asset",
            "priority": "Medium",
        },
    ]

    if category == "coffee":
        rows[2]["asset"] = "Brew process detail"
        rows[2]["notes"] = "Need brew ritual and bean texture proof"
    elif category == "supplement":
        rows[2]["asset"] = "Scoop/powder proof"
        rows[2]["notes"] = "Need clear scoop scale and mix context"
    elif category == "home-goods":
        rows[2]["asset"] = "Material/ambience detail"
        rows[2]["notes"] = "Need wax/glass texture and room context"

    return {"rows": rows, "category": category}


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


def stage_shoot_plan(
    scout: Dict[str, Any],
    preservation: Dict[str, Any],
    visual_gaps: Dict[str, Any],
    *,
    recommended_direction: str | None = None,
    strategy_rationale: str | None = None,
    explicit_shots: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    category = str(visual_gaps.get("category") or infer_category(scout, str(preservation.get("product_type", "")), ""))
    direction = recommended_direction or "Category-aware commerce with contextual lifestyle"
    rationale = strategy_rationale or (
        "Use source evidence to tune scenes by category while preserving strict product fidelity."
    )
    shots = explicit_shots if explicit_shots else default_shots_for_category(category)
    return {
        "recommended_direction": direction,
        "strategy_rationale": rationale,
        "category": category,
        "shots": shots,
    }


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


def stage_prompts(
    scout: Dict[str, Any],
    preservation: Dict[str, Any],
    shoot_plan: Dict[str, Any],
    *,
    brand: str,
    product: str,
) -> Dict[str, Any]:
    category = str(shoot_plan.get("category", "generic"))
    shots = shoot_plan.get("shots") or []
    strategy_rationale = str(shoot_plan.get("strategy_rationale", ""))
    evidence_tokens = keyword_evidence(scout, preservation, strategy_rationale)
    scene_hint = CATEGORY_SCENE_HINTS.get(category, CATEGORY_SCENE_HINTS["generic"])

    prompt_rows = []
    for idx, s in enumerate(shots, 1):
        row = {
            "shot_index": idx,
            "asset_id": f"shot-{idx:02d}",
            "shot_name": str(s.get("name", f"Shot {idx:02d}")),
            "use_case": str(s.get("category", "unknown")),
            "ratio": str(s.get("ratio", "1:1")),
            "channel": str(s.get("channel", "PDP")),
            "priority": str(s.get("priority", "Medium")),
            "prompt": compose_prompt(
                s,
                product,
                brand,
                str(preservation.get("tone", "balanced ecommerce")),
                scene_hint,
                [str(x) for x in preservation.get("must_preserve", [])],
                [str(x) for x in preservation.get("never_change", [])],
                [str(x) for x in preservation.get("distortion_risks", [])],
                evidence_tokens,
            ),
            "negative_constraints": [
                "no altered logo or label text",
                "no fake ingredient/claim badges",
                "no malformed hands or impossible anatomy",
                "no product count mismatch for intended SKU",
                "no prop occlusion hiding the primary label",
            ],
            "reroll_if_failed": (
                "If label legibility, pack geometry, or product count fails, reroll with flatter camera angle, "
                "cleaner background, and tighter product framing."
            ),
        }
        prompt_rows.append(row)

    return {"category": category, "shots": prompt_rows, "evidence_keywords": evidence_tokens}


def ensure_packet_dirs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    for d in ASSET_DIRS:
        (root / "assets" / d).mkdir(parents=True, exist_ok=True)
    (root / "assets" / "generated").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "exports").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def save_stage_artifacts(
    out_dir: Path,
    *,
    scout: Dict[str, Any] | None = None,
    preservation: Dict[str, Any] | None = None,
    visual_gaps: Dict[str, Any] | None = None,
    shoot_plan: Dict[str, Any] | None = None,
    prompts: Dict[str, Any] | None = None,
) -> None:
    if scout is not None:
        dump_json(out_dir / "scout.json", scout)
    if preservation is not None:
        dump_json(out_dir / "preservation.json", preservation)
    if visual_gaps is not None:
        dump_json(out_dir / "visual-gaps.json", visual_gaps)
    if shoot_plan is not None:
        dump_json(out_dir / "shoot-plan.json", shoot_plan)
    if prompts is not None:
        dump_json(out_dir / "prompts.json", prompts)


def render_packet_docs(
    out_dir: Path,
    *,
    brand: str,
    product: str,
    product_url: str,
    scout: Dict[str, Any],
    preservation: Dict[str, Any],
    visual_gaps: Dict[str, Any],
    shoot_plan: Dict[str, Any],
    prompts: Dict[str, Any],
) -> None:
    ensure_packet_dirs(out_dir)

    category = str(shoot_plan.get("category", "generic"))
    source_snapshot = {
        "title": clean_text(str(scout.get("title", ""))),
        "h1": scout.get("h1", []),
        "meta_description": clean_text(str(scout.get("meta_description") or scout.get("og_description") or "")),
        "top_image_urls": top_images(scout),
        "degraded_mode": bool(scout.get("degraded_mode", True)),
    }

    brand_analysis = (
        "# Brand Analysis\n\n"
        f"- Brand: {brand}\n"
        f"- Product: {product}\n"
        f"- URL: {product_url or scout.get('url', 'not provided')}\n"
        "- Price tier: unknown\n"
        f"- Audience: {preservation.get('audience', 'unknown')}\n"
        f"- Tone: {preservation.get('tone', 'unknown')}\n"
        "- Palette: unknown\n"
        f"- Inferred product category: {category}\n\n"
        "## Structured Scout Extraction\n"
        f"- Product name: {scout.get('product_name', product)}\n"
        f"- Brand name: {scout.get('brand_name', brand)}\n"
        f"- Product type/category: {scout.get('product_type', 'unknown')} / {scout.get('product_category', category)}\n"
        f"- Price (detected): {scout.get('price', 'unknown')}\n"
        f"- Variants/options: {', '.join(scout.get('variants', [])) or 'none detected'}\n"
        f"- Claims/benefits: {', '.join(scout.get('claims_benefits', [])) or 'none detected'}\n"
        f"- Ingredients/materials/specs: {', '.join(scout.get('ingredients_materials_specs', [])) or 'none detected'}\n"
        f"- Packaging text candidates: {', '.join(scout.get('visible_packaging_text_candidates', [])) or 'none detected'}\n"
        f"- Extraction warnings: {', '.join(scout.get('extraction_warnings', [])) or 'none'}\n\n"
        "## Product Preservation Brief\n"
        f"- Product type: {preservation.get('product_type', 'unknown')}\n"
        f"- Must preserve: {', '.join(preservation.get('must_preserve', [])) or 'exact pack shape, label position, logo'}\n"
        f"- Can vary: {', '.join(preservation.get('can_vary', [])) or 'camera angle, scene context, background depth'}\n"
        f"- Never change: {', '.join(preservation.get('never_change', [])) or 'label claims, brand name spelling, package geometry'}\n"
        f"- Distortion risks: {', '.join(preservation.get('distortion_risks', [])) or 'text warping, cap geometry drift, scale mismatch'}\n"
        f"- Accuracy confidence: {preservation.get('accuracy_confidence', 'medium')}\n\n"
        "## Source Evidence Snapshot\n"
        f"- Source title: {source_snapshot.get('title', 'n/a')}\n"
        f"- Source H1: {', '.join(source_snapshot.get('h1', [])[:2]) if isinstance(source_snapshot.get('h1'), list) else 'n/a'}\n"
        f"- Source summary: {source_snapshot.get('meta_description', 'n/a')}\n"
        f"- Evidence keywords used in prompts: {', '.join(prompts.get('evidence_keywords', [])) or 'none'}\n"
    )

    visual_gaps_md = "# Visual Gap Audit\n\n| Asset Type | Status | Notes | Priority |\n|---|---|---|---|\n"
    rows = visual_gaps.get("rows") or []
    for row in rows:
        visual_gaps_md += (
            f"| {row.get('asset', 'Unknown')} | {row.get('status', 'Missing')} | "
            f"{row.get('notes', '')} | {row.get('priority', 'Medium')} |\n"
        )

    strategy = (
        "# Shoot Strategy\n\n"
        "## Candidate Directions\n"
        "1. Conversion-safe commerce precision\n"
        "2. Contextual lifestyle trust-build\n"
        "3. Social-native narrative moments\n\n"
        "## Recommended Direction\n"
        f"{shoot_plan.get('recommended_direction', 'Contextual lifestyle trust-build with commerce-safe fallbacks')}\n\n"
        "## Why\n"
        f"{shoot_plan.get('strategy_rationale', 'Prioritize conversion clarity first, then emotional context where it does not compromise product truth.')}\n\n"
        "## Category Lens\n"
        f"- Category: {category}\n"
        f"- Category scene guidance: {CATEGORY_SCENE_HINTS.get(category, CATEGORY_SCENE_HINTS['generic'])}\n"
    )

    shot_list = "# Shot List\n\n| # | Shot Name | Category | Ratio | Channel | Priority |\n|---:|---|---|---|---|---|\n"
    prompts_md = "# Generation Prompts\n\n"
    export_map = "# Export Map\n\n| Shot | Best Use | Why |\n|---|---|---|\n"

    for shot in prompts.get("shots", []):
        i = int(shot.get("shot_index", 0))
        shot_list += (
            f"| {i} | {shot.get('shot_name')} | {shot.get('use_case')} | {shot.get('ratio')} | "
            f"{shot.get('channel')} | {shot.get('priority')} |\n"
        )
        prompts_md += (
            f"## Shot {i:02d} - {shot.get('shot_name')}\n\n"
            f"**Use case:** {shot.get('use_case')}\n"
            f"**Aspect ratio:** {shot.get('ratio')}\n\n"
            "**Prompt:**\n"
            f"{shot.get('prompt')}\n\n"
            "**Negative constraints:**\n"
            + "\n".join(f"- {x}" for x in shot.get("negative_constraints", []))
            + "\n\n"
            "**Reroll if failed:**\n"
            f"{shot.get('reroll_if_failed', '')}\n\n"
        )
        export_map += (
            f"| {shot.get('shot_name')} | {shot.get('channel')} | "
            f"{shot.get('use_case')} shot for {category} category goals with preservation-first framing. |\n"
        )

    qa_rows = "\n".join([
        "| Product accuracy | 30 | TBD | |",
        "| Commerce usefulness | 20 | TBD | |",
        "| Brand fit | 15 | TBD | |",
        "| Scene realism | 15 | TBD | |",
        "| Visual clarity | 10 | TBD | |",
        "| AI artifact risk | 10 | TBD | |",
    ])
    qa = (
        "# QA Report\n\n"
        "## Run Status\n"
        "- Generation: Not Run (planning mode by default)\n"
        "- Automated QA: Not Run\n\n"
        "## Rubric\n"
        "| Criterion | Weight | Score | Notes |\n"
        "|---|---:|---:|---|\n"
        f"{qa_rows}\n\n"
        "## Automatic Rejection Triggers\n"
        "- label text changed\n"
        "- product geometry changed\n"
        "- unreadable key text\n"
        "- malformed hand interacting with product\n"
        "- fake claims/certification\n"
        "- product too small for commerce utility\n"
    )

    files = {
        "00-brand-analysis.md": brand_analysis,
        "01-visual-gap-audit.md": visual_gaps_md,
        "02-shoot-strategy.md": strategy,
        "03-shot-list.md": shot_list,
        "04-generation-prompts.md": (
            prompts_md
            + "## Manual Generation Runbook\n"
            + "1. Generate priority High shots first and keep all manifests.\n"
            + "2. Run ./scripts/qa-images.py after each generation batch.\n"
            + "3. Run ./scripts/reroll-failed.py to simulate or execute rerolls for failed shots.\n"
            + "4. Only package assets that pass QA or are manually approved.\n"
        ),
        "05-qa-report.md": qa,
        "06-export-map.md": export_map,
        "memory/visual-profile.md": "# Visual Profile\n\nApproved worlds, rejected worlds, and recurring style rules.\n",
        "memory/product-shot-memory.md": "# Product Shot Memory\n\nPrompt fragments that passed/failed and fidelity constraints.\n",
        "memory/assets.md": "# Assets Log\n\nTrack approved files and channel placements.\n",
    }

    for rel, content in files.items():
        write_file(out_dir / rel, content)


def default_output_dir(base_dir: Path, brand: str, product: str) -> Path:
    today = date.today().isoformat()
    return base_dir / slug(brand) / slug(product) / today
