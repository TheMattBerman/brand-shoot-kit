#!/usr/bin/env python3
"""Executable eval harness for Brand Shoot Kit (deterministic, no-spend)."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import importlib.util
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "evals" / "fixtures"
TMP = ROOT / "output" / "evals"
GOLDEN_ROOT = ROOT / "examples" / "golden-runs"

REQUIRED_ARTIFACTS = ["scout.json", "preservation.json", "visual-gaps.json", "shoot-plan.json", "prompts.json"]
REQUIRED_SCOUT_FIELDS = [
    "product_name",
    "brand_name",
    "product_type",
    "product_category",
    "price",
    "variants",
    "claims_benefits",
    "ingredients_materials_specs",
    "visible_packaging_text_candidates",
    "image_evidence",
    "field_confidence",
    "extraction_warnings",
]
MODULE_CMDS = [
    ["scripts/modules/brand_scout.py", "--scout-json", "examples/scout-samples/skincare-serum-scout.json", "--packet", "{packet}"],
    ["scripts/modules/product_preservation.py", "--packet", "{packet}"],
    ["scripts/modules/visual_gap_audit.py", "--packet", "{packet}"],
    ["scripts/modules/shoot_director.py", "--packet", "{packet}"],
    ["scripts/modules/prompt_factory.py", "--packet", "{packet}"],
    ["scripts/create-shoot-packet.py", "--artifacts-dir", "{packet}", "--out", "{packet}"],
    ["scripts/generate-images.py", "--packet", "{packet}"],
    ["scripts/modules/qa_reroll.py", "--packet", "{packet}", "--run-qa"],
    ["scripts/modules/export_packager.py", "--packet", "{packet}", "--out", "{packet}/assets/exports/final"],
    ["scripts/modules/memory_writer.py", "--packet", "{packet}"],
]


def run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    full = [str(ROOT / cmd[0]), *cmd[1:]]
    env = os.environ.copy()
    env["BSK_FORCE_SCRAPER"] = "curl"  # Evals must never make live Firecrawl calls.
    return subprocess.run(full, cwd=ROOT, text=True, capture_output=True, env=env)


def assert_true(condition: bool, message: str, errors: List[str]) -> None:
    if condition:
        print(f"PASS {message}")
    else:
        print(f"FAIL {message}")
        errors.append(message)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def ratio_matches(dimensions: tuple[int, int], ratio: str) -> bool:
    normalized = ratio.strip().lower().replace("x", ":")
    expected = {
        "1:1": (1, 1),
        "4:5": (4, 5),
        "9:16": (9, 16),
        "16:9": (16, 9),
    }
    if normalized not in expected:
        return False
    left, right = expected[normalized]
    width, height = dimensions
    return width * right == height * left


def run_packet_from_fixture(name: str, fixture: Path) -> Path:
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "scripts/run-brand-shoot.py",
        "--scout-json",
        str(fixture),
        "--out",
        str(out),
    ]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"run-brand-shoot failed for {name}: {proc.stderr.strip() or proc.stdout.strip()}")
    return out


def eval_artifacts_and_structured_extraction(errors: List[str]) -> Path:
    packet = run_packet_from_fixture("artifact-check", FIXTURES / "scout-coffee.json")
    for filename in REQUIRED_ARTIFACTS:
        path = packet / filename
        assert_true(path.exists(), f"artifact exists: {filename}", errors)
        if path.exists():
            try:
                payload = load_json(path)
                assert_true(isinstance(payload, dict), f"artifact valid JSON object: {filename}", errors)
            except Exception as exc:
                assert_true(False, f"artifact parseable JSON: {filename} ({exc})", errors)

    scout = load_json(packet / "scout.json")
    for field in REQUIRED_SCOUT_FIELDS:
        assert_true(field in scout, f"structured scout field exists: {field}", errors)
    assert_true(isinstance(scout.get("field_confidence"), dict), "field_confidence is an object", errors)
    assert_true(isinstance(scout.get("image_evidence"), list), "image_evidence is a list", errors)
    assert_true(
        isinstance(scout.get("extraction_warnings"), list),
        "extraction_warnings is a list",
        errors,
    )
    return packet


def eval_structured_shopify_extraction(errors: List[str]) -> None:
    packet = run_packet_from_fixture("structured-shopify", FIXTURES / "scout-shopify-rich.json")
    scout = load_json(packet / "scout.json")

    assert_true(str(scout.get("price", "")).startswith("$18"), "structured extraction prefers JSON-LD/Shopify price", errors)
    variants = [str(v).lower() for v in (scout.get("variants") or [])]
    assert_true(any("whole bean" in v for v in variants), "structured extraction captures Shopify variants", errors)
    specs = " | ".join(str(v) for v in (scout.get("ingredients_materials_specs") or []))
    assert_true("arabica" in specs.lower() or "origin" in specs.lower(), "structured extraction captures ingredients/specs", errors)
    packaging = " | ".join(str(v) for v in (scout.get("visible_packaging_text_candidates") or []))
    assert_true("net wt" in packaging.lower() or "single origin" in packaging.lower(), "structured extraction captures packaging text", errors)
    warnings = [str(v) for v in (scout.get("extraction_warnings") or [])]
    assert_true(
        any("structured_source:" in w and "none_detected" not in w for w in warnings),
        "structured extraction records structured source hint",
        errors,
    )


def eval_prompt_differentiation(errors: List[str]) -> None:
    coffee_packet = run_packet_from_fixture("category-coffee", FIXTURES / "scout-coffee.json")
    skin_packet = run_packet_from_fixture("category-skin", ROOT / "examples" / "scout-samples" / "skincare-serum-scout.json")

    coffee = load_json(coffee_packet / "prompts.json")
    skin = load_json(skin_packet / "prompts.json")
    coffee_texts = [str(s.get("prompt", "")) for s in coffee.get("shots", [])]
    skin_texts = [str(s.get("prompt", "")) for s in skin.get("shots", [])]

    assert_true(len(coffee_texts) >= 8, "coffee prompts generated", errors)
    assert_true(len(skin_texts) >= 8, "skincare prompts generated", errors)

    overlap = len(set(coffee_texts) & set(skin_texts))
    max_allowed = max(1, min(len(coffee_texts), len(skin_texts)) // 5)
    assert_true(overlap <= max_allowed, "prompt overlap is not clone-level across fixtures", errors)
    assert_true(
        "coffee bag front label/artwork as the primary subject" in "\n".join(coffee_texts).lower(),
        "coffee prompts include bag-label dominance guidance",
        errors,
    )
    coffee_constraints = [
        c.lower()
        for shot in (coffee.get("shots") or [])
        for c in (shot.get("negative_constraints") or [])
    ]
    assert_true(
        any("coffee-specific: no hero mug/cup-only composition" in c for c in coffee_constraints),
        "coffee prompts include mug/beans suppression constraints",
        errors,
    )


def eval_category_taxonomy_baselines(errors: List[str]) -> None:
    fixtures = {
        "coffee": FIXTURES / "scout-coffee.json",
        "coffee_creamy_regression": FIXTURES / "scout-coffee-creamy.json",
        "supplement": FIXTURES / "scout-supplement.json",
        "cleaning": FIXTURES / "scout-cleaning-kit.json",
        "skincare": ROOT / "examples" / "scout-samples" / "skincare-serum-scout.json",
    }
    expected_terms = {
        "coffee": "clean front pack hero",
        "coffee_creamy_regression": "clean front pack hero",
        "supplement": "clean front tub hero",
        "cleaning": "clean front kit hero",
        "skincare": "clean front label hero",
    }

    for category, fixture in fixtures.items():
        packet = run_packet_from_fixture(f"category-baseline-{category}", fixture)
        shoot_plan = load_json(packet / "shoot-plan.json")
        prompts = load_json(packet / "prompts.json")
        inferred = str(shoot_plan.get("category", ""))
        expected_category = "coffee" if category == "coffee_creamy_regression" else category
        assert_true(inferred == expected_category, f"category baseline inferred as {expected_category}", errors)
        shot_names = [str(s.get("shot_name", "")).lower() for s in (prompts.get("shots") or [])]
        assert_true(any(expected_terms[category] in name for name in shot_names), f"{category} baseline shots include category-specific template", errors)


def eval_module_entrypoints(errors: List[str]) -> None:
    packet = TMP / "module-entrypoints"
    if packet.exists():
        shutil.rmtree(packet)
    packet.mkdir(parents=True, exist_ok=True)

    for cmd_template in MODULE_CMDS:
        cmd = [c.format(packet=str(packet)) for c in cmd_template]
        proc = run(cmd)
        label = " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))
        assert_true(proc.returncode == 0, f"module command succeeds: {label}", errors)

    for filename in REQUIRED_ARTIFACTS:
        assert_true((packet / filename).exists(), f"module output present: {filename}", errors)
    assert_true((packet / "assets" / "generated" / "qa-results.json").exists(), "module output present: qa-results.json", errors)
    assert_true(
        (packet / "assets" / "generated" / "reroll-manifest.json").exists(),
        "module output present: reroll-manifest.json",
        errors,
    )
    assert_true(
        (packet / "assets" / "exports" / "final" / "export-manifest.json").exists(),
        "module output present: export-manifest.json",
        errors,
    )
    for memory_name in ["visual-profile.md", "product-shot-memory.md", "assets.md"]:
        assert_true((packet / "memory" / memory_name).exists(), f"module output present: memory/{memory_name}", errors)


def eval_dry_run_loop(errors: List[str]) -> None:
    packet = run_packet_from_fixture("dry-run-loop", ROOT / "examples" / "scout-samples" / "skincare-serum-scout.json")
    steps = [
        ["scripts/generate-images.py", "--packet", str(packet)],
        ["scripts/qa-images.py", "--packet", str(packet)],
        ["scripts/reroll-failed.py", "--packet", str(packet)],
        ["scripts/export-packager.py", "--packet", str(packet), "--out", str(packet / "assets" / "exports" / "final")],
    ]
    for cmd in steps:
        proc = run(cmd)
        label = " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))
        assert_true(proc.returncode == 0, f"command succeeds: {label}", errors)

    assert_true((packet / "assets" / "generated" / "generation-manifest.json").exists(), "generation manifest produced", errors)
    assert_true((packet / "assets" / "generated" / "qa-results.json").exists(), "qa results produced", errors)
    assert_true((packet / "assets" / "generated" / "reroll-manifest.json").exists(), "reroll manifest produced", errors)
    assert_true((packet / "assets" / "exports" / "final" / "export-manifest.json").exists(), "export manifest produced", errors)


def eval_export_rendering_metadata(errors: List[str]) -> None:
    packet = run_packet_from_fixture("export-rendering", FIXTURES / "scout-coffee.json")
    for cmd in [
        ["scripts/generate-images.py", "--packet", str(packet), "--limit", "2"],
        ["scripts/qa-images.py", "--packet", str(packet)],
        ["scripts/reroll-failed.py", "--packet", str(packet)],
        ["scripts/export-packager.py", "--packet", str(packet), "--out", str(packet / "assets" / "exports" / "final")],
    ]:
        proc = run(cmd)
        label = " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))
        assert_true(proc.returncode == 0, f"command succeeds: {label}", errors)

    export_manifest = load_json(packet / "assets" / "exports" / "final" / "export-manifest.json")
    records = export_manifest.get("records") or []
    packaged = [r for r in records if r.get("status") == "packaged"]
    assert_true(bool(packaged), "export rendering eval has packaged records", errors)
    for record in packaged:
        for output in record.get("outputs") or []:
            dims = output.get("output_dimensions")
            assert_true(
                isinstance(dims, list) and len(dims) == 2 and all(isinstance(v, int) and v > 0 for v in dims),
                "export output has output_dimensions",
                errors,
            )
            render_mode = str(output.get("render_mode", ""))
            assert_true(render_mode.startswith("render:") or render_mode.startswith("copy:"), "export output has render_mode", errors)
            path = Path(str(output.get("path", "")))
            assert_true(path.exists(), "rendered export file exists", errors)
            if path.exists() and isinstance(dims, list) and len(dims) == 2:
                actual_dims = parse_png_dimensions(path)
                assert_true(actual_dims == (dims[0], dims[1]), "rendered export dimensions match manifest", errors)


def eval_ratio_aware_generation_manifest(errors: List[str]) -> None:
    packet = run_packet_from_fixture("ratio-aware-dry-run", FIXTURES / "scout-coffee.json")
    proc = run(["scripts/generate-images.py", "--packet", str(packet)])
    assert_true(proc.returncode == 0, "ratio-aware dry-run generation succeeds", errors)
    if proc.returncode != 0:
        return

    manifest_path = packet / "assets" / "generated" / "generation-manifest.json"
    assert_true(manifest_path.exists(), "ratio-aware generation manifest exists", errors)
    if not manifest_path.exists():
        return

    payload = load_json(manifest_path)
    entries = payload.get("entries") or []
    assert_true(len(entries) >= 4, "ratio-aware eval has multiple generated entries", errors)
    for entry in entries:
        ratio = str(entry.get("requested_ratio", ""))
        provider_size = entry.get("provider_size")
        final_dimensions = entry.get("final_dimensions")
        image_path = Path(str(entry.get("image_path", "")))

        assert_true(ratio in {"1:1", "4:5", "9:16", "16:9"}, f"entry has normalized requested_ratio: {ratio}", errors)
        assert_true(isinstance(provider_size, str) and "x" in provider_size, "entry has provider_size", errors)
        assert_true(
            isinstance(final_dimensions, list)
            and len(final_dimensions) == 2
            and all(isinstance(v, int) and v > 0 for v in final_dimensions),
            "entry has final_dimensions",
            errors,
        )
        if isinstance(final_dimensions, list) and len(final_dimensions) == 2 and all(isinstance(v, int) for v in final_dimensions):
            expected_dims = (int(final_dimensions[0]), int(final_dimensions[1]))
            assert_true(ratio_matches(expected_dims, ratio), f"manifest final_dimensions match requested ratio: {ratio}", errors)
            assert_true(image_path.exists(), f"generated file exists: {image_path.name}", errors)
            if image_path.exists():
                actual_dims = parse_png_dimensions(image_path)
                assert_true(actual_dims is not None, f"generated file parseable as PNG: {image_path.name}", errors)
                if actual_dims is not None:
                    assert_true(actual_dims == expected_dims, f"dry-run PNG dimensions match manifest: {image_path.name}", errors)


def eval_prompt_scale_human_context_guidance(errors: List[str]) -> None:
    packet = run_packet_from_fixture("prompt-guidance-check", FIXTURES / "scout-coffee.json")
    prompts = load_json(packet / "prompts.json")
    shots = prompts.get("shots") or []
    assert_true(len(shots) >= 8, "prompt-guidance eval has generated shots", errors)
    if not shots:
        return

    scale_values = {str(s.get("scale_guidance", "")) for s in shots}
    human_values = {str(s.get("human_guidance", "")) for s in shots}
    context_values = {str(s.get("context_guidance", "")) for s in shots}
    prompt_texts = [str(s.get("prompt", "")).lower() for s in shots]
    joined_prompts = "\n".join(prompt_texts)

    assert_true(len(scale_values) >= 4, "scale guidance varies across shots", errors)
    assert_true(len(human_values) >= 2, "human guidance varies across shots", errors)
    assert_true(len(context_values) >= 3, "context guidance varies across shots", errors)
    assert_true("human guidance:" in joined_prompts, "prompts include explicit human guidance text", errors)
    assert_true("scale guidance:" in joined_prompts, "prompts include explicit shot-specific scale guidance text", errors)
    assert_true("context guidance:" in joined_prompts, "prompts include explicit context guidance text", errors)
    assert_true("32-48%" not in joined_prompts, "prompts no longer force fixed 32-48% occupancy", errors)
    assert_true(any("in-use" in p for p in prompt_texts), "prompts include product-in-use guidance", errors)
    assert_true(any("bundle" in p or "contents" in p for p in prompt_texts), "prompts include bundle/contents guidance", errors)


def eval_reference_image_manifest(errors: List[str]) -> None:
    packet = run_packet_from_fixture("reference-image", FIXTURES / "scout-coffee.json")
    reference_image = FIXTURES / "reference-product.png"
    assert_true(reference_image.exists(), "reference fixture exists", errors)
    if not reference_image.exists():
        return

    proc = run(
        [
            "scripts/generate-images.py",
            "--packet",
            str(packet),
            "--limit",
            "1",
            "--overwrite",
            "--reference-image",
            str(reference_image),
        ]
    )
    assert_true(proc.returncode == 0, "reference-image dry generation command succeeds", errors)
    if proc.returncode != 0:
        return

    manifest = load_json(packet / "assets" / "generated" / "generation-manifest.json")
    ref_path = manifest.get("reference_image_path")
    assert_true(isinstance(ref_path, str) and ref_path != "", "manifest run metadata has reference_image_path", errors)
    assert_true(manifest.get("reference_image_url") is None, "manifest run metadata has null reference_image_url for local source", errors)
    entries = manifest.get("entries") or []
    assert_true(len(entries) == 1, "reference-image eval limited to one shot", errors)
    if entries:
        entry = entries[0]
        assert_true(
            isinstance(entry.get("reference_image_path"), str) and entry.get("reference_image_path") != "",
            "entry metadata has reference_image_path",
            errors,
        )
        assert_true(
            entry.get("reference_image_url") is None,
            "entry metadata has null reference_image_url for local source",
            errors,
        )
        cache_path = Path(str(entry.get("reference_image_path")))
        assert_true(cache_path.exists(), "cached reference image file exists", errors)


def eval_codex_native_handoff(errors: List[str]) -> None:
    packet = run_packet_from_fixture("codex-native-handoff", FIXTURES / "scout-coffee.json")
    proc = run(
        [
            "scripts/generate-images.py",
            "--packet",
            str(packet),
            "--limit",
            "2",
            "--provider",
            "codex-native",
        ]
    )
    assert_true(proc.returncode == 0, "codex-native generation handoff command succeeds", errors)
    if proc.returncode != 0:
        return

    manifest_path = packet / "assets" / "generated" / "generation-manifest.json"
    requests_path = packet / "assets" / "generated" / "native-generation-requests.json"
    assert_true(manifest_path.exists(), "codex-native manifest exists", errors)
    assert_true(requests_path.exists(), "codex-native request handoff exists", errors)
    if not manifest_path.exists() or not requests_path.exists():
        return

    manifest = load_json(manifest_path)
    handoff = load_json(requests_path)
    entries = manifest.get("entries") or []
    requests = handoff.get("requests") or []
    assert_true(manifest.get("provider") == "codex-native", "codex-native manifest records provider", errors)
    assert_true(handoff.get("status") == "awaiting_agent_generation", "codex-native handoff awaits agent", errors)
    assert_true(len(entries) == 2, "codex-native manifest respects shot limit", errors)
    assert_true(len(requests) == 2, "codex-native handoff respects shot limit", errors)
    assert_true(manifest.get("native_generation_requests_path") == str(requests_path), "manifest links native handoff", errors)

    for entry, request in zip(entries, requests):
        image_path = Path(str(entry.get("image_path", "")))
        assert_true(entry.get("status") == "awaiting_agent_generation", "codex-native entry is pending", errors)
        assert_true(entry.get("requires_agent") is True, "codex-native entry requires agent", errors)
        assert_true(entry.get("dry_run") is False, "codex-native entry is not dry-run placeholder", errors)
        assert_true(entry.get("postprocess_mode") == "pending:codex-native-agent", "codex-native entry has pending postprocess mode", errors)
        assert_true(not image_path.exists(), "codex-native does not create placeholder image", errors)
        assert_true(request.get("output_path") == str(image_path), "codex-native request points to entry image_path", errors)
        assert_true(isinstance(request.get("prompt"), str) and request.get("prompt"), "codex-native request includes prompt", errors)


def eval_codex_native_preserves_auto_reference(errors: List[str]) -> None:
    module_path = ROOT / "scripts" / "generate-images.py"
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("generate_images_for_eval", module_path)
    assert_true(spec is not None and spec.loader is not None, "generate-images module loadable for reference eval", errors)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    packet = TMP / "codex-native-auto-reference"
    packet.mkdir(parents=True, exist_ok=True)
    cached_reference = packet / "assets" / "reference-images" / "cached-product.png"
    cached_reference.parent.mkdir(parents=True, exist_ok=True)
    cached_reference.write_bytes(b"reference")

    original_pick = module.pick_auto_reference_url
    original_cache = module.cache_reference_image
    try:
        module.pick_auto_reference_url = lambda _packet_dir: "https://cdn.example.com/images/product-packshot.png"
        module.cache_reference_image = lambda source, *, packet_dir, allow_network: {
            "reference_image_path": str(cached_reference),
            "reference_image_url": source,
        }
        ref_path, ref_url, notes, source_mode = module.resolve_reference_image(
            args=Namespace(reference_image=None, auto_reference_image=None, packet=str(packet)),
            packet_dir=packet,
            mode="codex-native",
        )
    finally:
        module.pick_auto_reference_url = original_pick
        module.cache_reference_image = original_cache

    assert_true(ref_path == cached_reference, "codex-native auto reference is cached locally", errors)
    assert_true(ref_url == "https://cdn.example.com/images/product-packshot.png", "codex-native auto reference keeps source URL", errors)
    assert_true(source_mode == "auto", "codex-native auto reference records source mode", errors)
    assert_true("reference_image_url:not_cached_for_codex_native_handoff" not in notes, "codex-native no longer skips URL caching", errors)


def eval_live_generation_requires_live_flag(errors: List[str]) -> None:
    packet = run_packet_from_fixture("provider-live-rejected", FIXTURES / "scout-coffee.json")
    proc = run(["scripts/generate-images.py", "--packet", str(packet), "--provider", "live"])
    assert_true(proc.returncode != 0, "--provider live is not accepted as a live-spend gate", errors)
    assert_true("invalid choice" in proc.stderr, "--provider live reports invalid choice", errors)


def eval_reference_selection_ranking(errors: List[str]) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from reference_selector import pick_auto_reference_url_from_scout  # type: ignore

    scout = {
        "product_name": "Summit Roast Coffee",
        "brand_name": "Alpine Goods",
        "image_evidence": [
            {"url": "https://production-beam-widgets.beamimpact.com/chains/img/chainNonprofit/causeDisplayIcon/c...", "confidence": 0.99, "rank": 0},
            {"url": "https://cdn.example.com/assets/logo.svg", "confidence": 0.97, "rank": 1},
            {"url": "https://cdn.example.com/images/nutrition-facts-panel.jpg", "confidence": 0.96, "rank": 2},
            {"url": "https://cdn.example.com/images/summit-roast-front-packshot.jpg", "confidence": 0.81, "rank": 4},
        ],
        "image_urls": [
            "https://cdn.example.com/images/review-stars.png",
            "https://cdn.example.com/images/summit-roast-hero-product.jpg",
        ],
    }
    picked = pick_auto_reference_url_from_scout(scout)
    assert_true(
        picked == "https://cdn.example.com/images/summit-roast-front-packshot.jpg",
        "reference selection prefers product/package imagery over logo/nutrition/review assets",
        errors,
    )


def eval_review_artifact_packager(errors: List[str]) -> None:
    packet = run_packet_from_fixture("review-pack", FIXTURES / "scout-coffee.json")
    for cmd in [
        ["scripts/generate-images.py", "--packet", str(packet), "--limit", "3"],
        ["scripts/qa-images.py", "--packet", str(packet)],
        ["scripts/reroll-failed.py", "--packet", str(packet)],
        ["scripts/export-packager.py", "--packet", str(packet), "--out", str(packet / "assets" / "exports" / "final")],
        ["scripts/package-review-artifacts.py", "--packet", str(packet)],
    ]:
        proc = run(cmd)
        label = " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))
        assert_true(proc.returncode == 0, f"command succeeds: {label}", errors)

    review_root = packet / "assets" / "review"
    magic_index = packet / "index.html"
    template = review_root / "human-review-template.json"
    contact = review_root / "contact-sheet.html"
    manifest = review_root / "artifact-pack-manifest.json"
    assert_true(magic_index.exists(), "review artifact exists: packet-root index.html", errors)
    assert_true(template.exists(), "review artifact exists: human-review-template.json", errors)
    assert_true(contact.exists(), "review artifact exists: contact-sheet.html", errors)
    assert_true(manifest.exists(), "review artifact exists: artifact-pack-manifest.json", errors)
    if magic_index.exists():
        html_text = magic_index.read_text(encoding="utf-8")
        assert_true("id=\"generated-gallery\"" in html_text, "magic frontend has generated gallery marker", errors)
        assert_true("generated-image-card" in html_text, "magic frontend has generated image cards", errors)
        assert_true("data-bsk-magic-moment=\"true\"" in html_text, "magic frontend has magic moment marker", errors)
    if manifest.exists():
        payload = load_json(manifest)
        summary = payload.get("summary", {})
        decisions = summary.get("suggested_decisions", {})
        assert_true(isinstance(decisions, dict), "review artifact summary includes suggested_decisions", errors)
        assert_true(
            {"approve", "reroll", "reject"}.issubset(set(decisions.keys())),
            "review artifact summary has approve/reroll/reject keys",
            errors,
        )

    # Scout scraper provenance is rendered onto index.html.
    # The label may read "Scout: curl", "Scout: Firecrawl /v2/scrape · ...", or
    # "Scout: unknown" when the scout came from a --scout-json fixture (no adapter ran).
    # All three forms satisfy the contract: the provenance section is present.
    index_html = packet / "index.html"
    if index_html.exists():
        content = index_html.read_text(encoding="utf-8")
        assert_true(
            "Scout: " in content,
            "index.html includes scout scraper provenance",
            errors,
        )


def eval_live_proof_no_spend_defaults(errors: List[str]) -> None:
    out = TMP / "live-proof-no-spend"
    if out.exists():
        shutil.rmtree(out)
    proc = run(
        [
            "scripts/run-live-proof.sh",
            "--url",
            "https://example.com/products/no-spend-proof",
            "--out",
            str(out),
            "--max-shots",
            "2",
        ]
    )
    assert_true(proc.returncode == 0, "live-proof default run succeeds in dry no-spend mode", errors)
    if proc.returncode != 0:
        return
    gen = load_json(out / "assets" / "generated" / "generation-manifest.json")
    assert_true(gen.get("provider") == "dry-run", "live-proof default generation provider is dry-run", errors)
    run_log = out / "live-proof-commands.log"
    assert_true(run_log.exists(), "live-proof command log exists", errors)
    if run_log.exists():
        cmd_text = run_log.read_text(encoding="utf-8")
        assert_true(" --live" not in cmd_text, "live-proof dry run does not invoke live flags", errors)
    summary = load_json(out / "assets" / "review" / "artifact-pack-manifest.json").get("summary", {})
    decision_keys = set((summary.get("suggested_decisions") or {}).keys())
    assert_true({"approve", "reroll", "reject"}.issubset(decision_keys), "live-proof review pack has decision summary keys", errors)
    magic_index = out / "index.html"
    assert_true(magic_index.exists(), "live-proof packet-root index.html exists", errors)
    if magic_index.exists():
        html_text = magic_index.read_text(encoding="utf-8")
        assert_true("id=\"generated-gallery\"" in html_text, "live-proof index has generated gallery marker", errors)
        assert_true("generated-image-card" in html_text, "live-proof index has generated image cards", errors)


def eval_golden_bundle_completeness(errors: List[str]) -> None:
    build = run(["scripts/build-golden-runs.sh"])
    assert_true(build.returncode == 0, "golden bundles build successfully", errors)
    check = run(["scripts/build-golden-runs.sh", "--check"])
    assert_true(check.returncode == 0, "golden bundles pass completeness check", errors)

    bundles = sorted([p for p in GOLDEN_ROOT.iterdir() if p.is_dir() and p.name != "__pycache__"])
    assert_true(len(bundles) >= 4, "at least four golden bundles exist", errors)
    assert_true(
        {"coffee-roast", "skincare-serum", "supplement-greens", "cleaning-kit"}.issubset({b.name for b in bundles}),
        "golden bundles include coffee/skincare/supplement/cleaning",
        errors,
    )
    # firecrawl-baseline is a scout-only golden run; skip full-pipeline artifact checks.
    SCOUT_ONLY_BUNDLES = {"firecrawl-baseline"}
    for bundle in bundles:
        if bundle.name in SCOUT_ONLY_BUNDLES:
            continue
        required = [
            bundle / "input" / "scout-fixture.json",
            bundle / "scout.json",
            bundle / "preservation.json",
            bundle / "visual-gaps.json",
            bundle / "shoot-plan.json",
            bundle / "prompts.json",
            bundle / "00-brand-analysis.md",
            bundle / "04-generation-prompts.md",
            bundle / "assets" / "generated" / "generation-manifest.json",
            bundle / "assets" / "generated" / "qa-results.json",
            bundle / "assets" / "generated" / "reroll-manifest.json",
            bundle / "assets" / "exports" / "final" / "export-manifest.json",
            bundle / "README.md",
        ]
        for path in required:
            assert_true(path.exists(), f"golden bundle file exists: {path.relative_to(ROOT)}", errors)


def eval_live_proof_tooling(errors: List[str]) -> None:
    script = ROOT / "scripts" / "run-live-proof.sh"
    review_script = ROOT / "scripts" / "package-review-artifacts.py"
    assert_true(script.exists(), "live proof script exists", errors)
    assert_true(script.stat().st_mode & 0o111 != 0, "live proof script is executable", errors)
    assert_true(review_script.exists(), "review packager script exists", errors)
    assert_true(review_script.stat().st_mode & 0o111 != 0, "review packager script is executable", errors)

    proc = run(["scripts/run-live-proof.sh", "--help"])
    assert_true(proc.returncode == 0, "live proof help command succeeds", errors)
    proc2 = run(["scripts/package-review-artifacts.py", "--help"])
    assert_true(proc2.returncode == 0, "review packager help command succeeds", errors)


def eval_scraper_adapters(errors: List[str]) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import adapters  # noqa: F401
        assert_true(True, "adapters package importable", errors)
    except Exception as exc:
        assert_true(False, f"adapters package importable ({exc})", errors)
        return

    # Curl adapter: smoke test against a static HTML fixture (file:// URL works via curl).
    fixture_html = ROOT / "evals" / "fixtures" / "html" / "shopify-coffee.html"
    if not fixture_html.exists():
        # Skip cleanly if the HTML fixture isn't created yet (Task 2 step 3).
        return

    from adapters import curl_scrape
    payload = curl_scrape.scrape(f"file://{fixture_html}")
    assert_true(payload.get("scraper") == "curl", "curl adapter sets scraper field", errors)
    assert_true(payload.get("degraded_mode") is True, "curl adapter sets degraded_mode=true", errors)
    assert_true(isinstance(payload.get("image_urls"), list), "curl adapter returns image_urls list", errors)
    assert_true(isinstance(payload.get("json_ld"), list), "curl adapter returns json_ld list", errors)
    assert_true(payload.get("url") == f"file://{fixture_html}", "curl adapter echoes input url", errors)

    # Firecrawl adapter: fixture mode
    fixture_dir = ROOT / "evals" / "fixtures" / "firecrawl"
    if not (fixture_dir / "README.md").exists():
        return  # adapter not yet built

    from adapters import firecrawl_scrape
    fixture_url = "https://example.com/products/sample"
    payload = firecrawl_scrape.scrape(fixture_url, fixture_dir=fixture_dir)
    assert_true(payload.get("scraper") == "firecrawl", "firecrawl adapter sets scraper field", errors)
    assert_true(payload.get("degraded_mode") is False, "firecrawl adapter sets degraded_mode=false", errors)
    assert_true(payload.get("url") == fixture_url, "firecrawl adapter echoes input url", errors)
    assert_true(isinstance(payload.get("image_urls"), list), "firecrawl adapter returns image_urls list", errors)
    assert_true(isinstance(payload.get("structured_product"), dict), "firecrawl adapter populates structured_product", errors)
    sp = payload.get("structured_product") or {}
    assert_true(sp.get("brand") == "Sample Roastery", "firecrawl structured_product.brand from fixture", errors)
    assert_true(payload.get("main_image_url", "").startswith("https://"), "firecrawl adapter populates main_image_url", errors)
    prov = payload.get("scrape_provenance") or {}
    assert_true(prov.get("scraper") == "firecrawl", "firecrawl scrape_provenance.scraper", errors)
    assert_true(prov.get("fixture_used") is not None, "firecrawl scrape_provenance.fixture_used set in fixture mode", errors)

    # Firecrawl adapter: live path requires a key
    saved_key = os.environ.pop("FIRECRAWL_API_KEY", None)
    saved_dir = os.environ.pop("BSK_FIRECRAWL_FIXTURE_DIR", None)
    try:
        from adapters.firecrawl_scrape import FirecrawlScrapeError
        try:
            firecrawl_scrape.scrape("https://example.com/no-fixture-no-key")
            assert_true(False, "firecrawl adapter without key/fixture raises", errors)
        except FirecrawlScrapeError as e:
            assert_true("api_key" in e.kind or "fixture_missing" in e.kind,
                        "firecrawl adapter raises clear error without key/fixture", errors)
    finally:
        if saved_key is not None:
            os.environ["FIRECRAWL_API_KEY"] = saved_key
        if saved_dir is not None:
            os.environ["BSK_FIRECRAWL_FIXTURE_DIR"] = saved_dir

    # Dispatcher: --scraper curl forces curl regardless of env
    saved_key = os.environ.pop("FIRECRAWL_API_KEY", None)
    os.environ["FIRECRAWL_API_KEY"] = "fake-key-should-not-be-used"
    try:
        proc = run([
            "scripts/modules/brand_scout.py",
            "--url", f"file://{ROOT}/evals/fixtures/html/shopify-coffee.html",
            "--out", str(TMP / "dispatcher-curl-forced.json"),
            "--scraper", "curl",
        ])
        assert_true(proc.returncode == 0, "dispatcher --scraper curl exits 0 even with key set", errors)
        if proc.returncode == 0:
            payload = load_json(TMP / "dispatcher-curl-forced.json")
            assert_true(payload.get("scrape_provenance", {}).get("scraper") == "curl",
                        "dispatcher --scraper curl produces curl provenance", errors)
            assert_true(payload.get("scrape_provenance", {}).get("forced_by") == "--scraper",
                        "dispatcher records forced_by=--scraper", errors)
    finally:
        if saved_key is not None:
            os.environ["FIRECRAWL_API_KEY"] = saved_key
        else:
            os.environ.pop("FIRECRAWL_API_KEY", None)

    # Dispatcher: --scraper firecrawl without key fails loudly with exit 2
    os.environ.pop("FIRECRAWL_API_KEY", None)
    proc = run([
        "scripts/modules/brand_scout.py",
        "--url", "https://example.com/products/sample",
        "--out", str(TMP / "dispatcher-firecrawl-no-key.json"),
        "--scraper", "firecrawl",
    ])
    assert_true(proc.returncode == 2, "dispatcher --scraper firecrawl without key exits 2", errors)
    assert_true("--scraper curl" in proc.stderr, "dispatcher error message includes --scraper curl recovery hint", errors)

    # run-brand-shoot.py forwards --scraper to the dispatcher.
    suite_out = TMP / "suite-scraper-curl"
    proc_suite = run([
        "scripts/run-brand-shoot.py",
        "--url", f"file://{ROOT}/evals/fixtures/html/shopify-coffee.html",
        "--out", str(suite_out),
        "--scraper", "curl",
        "--stage", "scout",
        "--skip-validate",
    ])
    assert_true(proc_suite.returncode == 0,
                f"run-brand-shoot --scraper curl exits 0 ({proc_suite.stderr.strip()[:200]})", errors)
    if proc_suite.returncode == 0:
        scout_json = suite_out / "scout.json"
        assert_true(scout_json.exists(), "run-brand-shoot writes scout.json with --scraper", errors)

    # Eval harness contract: run() forces BSK_FORCE_SCRAPER=curl on subprocess scout calls,
    # so even with FIRECRAWL_API_KEY set in the parent shell, evals never make live Firecrawl calls.
    saved_key = os.environ.pop("FIRECRAWL_API_KEY", None)
    os.environ["FIRECRAWL_API_KEY"] = "fake-key-evals-must-not-use"
    try:
        proc2 = run([
            "scripts/modules/brand_scout.py",
            "--url", f"file://{ROOT}/evals/fixtures/html/shopify-coffee.html",
            "--out", str(TMP / "harness-force-curl.json"),
        ])
        assert_true(proc2.returncode == 0, "harness run() with key set: brand_scout exits 0", errors)
        assert_true("scraper=curl" in proc2.stderr,
                    "harness run() forces BSK_FORCE_SCRAPER=curl on subprocess scout calls", errors)
    finally:
        if saved_key is not None:
            os.environ["FIRECRAWL_API_KEY"] = saved_key
        else:
            os.environ.pop("FIRECRAWL_API_KEY", None)


def eval_firecrawl_structured_preference(errors: List[str]) -> None:
    """When Firecrawl populates structured_product, enrich_scout prefers those values."""
    out = TMP / "firecrawl-structured-preference.json"
    env = os.environ.copy()
    env["BSK_FIRECRAWL_FIXTURE_DIR"] = str(ROOT / "evals" / "fixtures" / "firecrawl")
    proc = subprocess.run(
        [
            str(ROOT / "scripts" / "modules" / "brand_scout.py"),
            "--url", "https://example.com/products/sample",
            "--out", str(out),
            "--scraper", "firecrawl",
        ],
        cwd=ROOT, text=True, capture_output=True, env=env,
    )
    assert_true(proc.returncode == 0, "brand_scout firecrawl-fixture run exits 0", errors)
    if proc.returncode != 0:
        return
    scout = load_json(out)
    assert_true(scout.get("brand_name", "").lower() == "sample roastery",
                "enrich_scout uses Firecrawl structured_product.brand", errors)
    assert_true(scout.get("product_name", "").lower() == "sample coffee",
                "enrich_scout uses Firecrawl structured_product.product_name", errors)
    assert_true(str(scout.get("price", "")).startswith("$18"),
                "enrich_scout uses Firecrawl structured_product.price", errors)
    image_evidence = scout.get("image_evidence") or []
    assert_true(any("sample-coffee-hero" in str(e.get("url", "")) for e in image_evidence),
                "enrich_scout image_evidence includes Firecrawl main_image_url", errors)


def eval_firecrawl_golden_run(errors: List[str]) -> None:
    """Run examples/golden-runs/firecrawl-baseline/run.sh and verify scout output."""
    golden_dir = GOLDEN_ROOT / "firecrawl-baseline"
    run_script = golden_dir / "run.sh"
    if not run_script.exists():
        assert_true(False, "firecrawl-baseline golden run script exists", errors)
        return
    out = TMP / "firecrawl-baseline"
    if out.exists():
        shutil.rmtree(out)
    proc = subprocess.run(
        [str(run_script), str(out)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert_true(proc.returncode == 0, f"firecrawl-baseline run.sh exits 0 ({proc.stderr.strip()[:200]})", errors)
    if proc.returncode != 0:
        return
    scout_path = out / "scout.json"
    assert_true(scout_path.exists(), "firecrawl-baseline produces scout.json", errors)
    if not scout_path.exists():
        return
    scout = load_json(scout_path)
    assert_true(scout.get("brand_name", "").lower() == "sample roastery",
                "firecrawl-baseline scout brand from fixture", errors)
    assert_true(scout.get("product_name", "").lower() == "sample coffee",
                "firecrawl-baseline scout product_name from fixture", errors)


def main() -> int:
    errors: List[str] = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    try:
        eval_artifacts_and_structured_extraction(errors)
        eval_structured_shopify_extraction(errors)
        eval_prompt_differentiation(errors)
        eval_category_taxonomy_baselines(errors)
        eval_prompt_scale_human_context_guidance(errors)
        eval_scraper_adapters(errors)
        eval_firecrawl_structured_preference(errors)
        eval_firecrawl_golden_run(errors)
        eval_module_entrypoints(errors)
        eval_dry_run_loop(errors)
        eval_export_rendering_metadata(errors)
        eval_ratio_aware_generation_manifest(errors)
        eval_reference_image_manifest(errors)
        eval_codex_native_handoff(errors)
        eval_codex_native_preserves_auto_reference(errors)
        eval_live_generation_requires_live_flag(errors)
        eval_reference_selection_ranking(errors)
        eval_review_artifact_packager(errors)
        eval_golden_bundle_completeness(errors)
        eval_live_proof_tooling(errors)
        eval_live_proof_no_spend_defaults(errors)
    except Exception as exc:
        print(f"FAIL harness runtime error: {exc}")
        errors.append(f"runtime error: {exc}")

    print("\nScrape policy: BSK_FORCE_SCRAPER=curl (evals never call Firecrawl live)")
    print(f"Summary: {len(errors)} failures")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
