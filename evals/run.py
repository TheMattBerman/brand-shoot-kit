#!/usr/bin/env python3
"""Executable eval harness for Brand Shoot Kit (deterministic, no-spend)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    return subprocess.run(full, cwd=ROOT, text=True, capture_output=True)


def assert_true(condition: bool, message: str, errors: List[str]) -> None:
    if condition:
        print(f"PASS {message}")
    else:
        print(f"FAIL {message}")
        errors.append(message)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def eval_golden_bundle_completeness(errors: List[str]) -> None:
    build = run(["scripts/build-golden-runs.sh"])
    assert_true(build.returncode == 0, "golden bundles build successfully", errors)
    check = run(["scripts/build-golden-runs.sh", "--check"])
    assert_true(check.returncode == 0, "golden bundles pass completeness check", errors)

    bundles = sorted([p for p in GOLDEN_ROOT.iterdir() if p.is_dir() and p.name != "__pycache__"])
    assert_true(len(bundles) >= 2, "at least two golden bundles exist", errors)
    for bundle in bundles:
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
    assert_true(script.exists(), "live proof script exists", errors)
    assert_true(script.stat().st_mode & 0o111 != 0, "live proof script is executable", errors)

    proc = run(["scripts/run-live-proof.sh", "--help"])
    assert_true(proc.returncode == 0, "live proof help command succeeds", errors)


def main() -> int:
    errors: List[str] = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    try:
        eval_artifacts_and_structured_extraction(errors)
        eval_prompt_differentiation(errors)
        eval_module_entrypoints(errors)
        eval_dry_run_loop(errors)
        eval_reference_image_manifest(errors)
        eval_golden_bundle_completeness(errors)
        eval_live_proof_tooling(errors)
    except Exception as exc:
        print(f"FAIL harness runtime error: {exc}")
        errors.append(f"runtime error: {exc}")

    print(f"\nSummary: {len(errors)} failures")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
