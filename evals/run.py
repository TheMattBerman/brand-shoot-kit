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
EVALS = ROOT / "evals"
FIXTURES = EVALS / "fixtures"
TMP = ROOT / "output" / "evals"


def run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)


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
        str(ROOT / "scripts" / "run-brand-shoot.py"),
        "--scout-json",
        str(fixture),
        "--out",
        str(out),
    ]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"run-brand-shoot failed for {name}: {proc.stderr.strip() or proc.stdout.strip()}")
    return out


def eval_artifacts(errors: List[str]) -> Path:
    packet = run_packet_from_fixture("artifact-check", FIXTURES / "scout-coffee.json")
    for filename in ["scout.json", "preservation.json", "visual-gaps.json", "shoot-plan.json", "prompts.json"]:
        path = packet / filename
        assert_true(path.exists(), f"artifact exists: {filename}", errors)
        if path.exists():
            try:
                payload = load_json(path)
                assert_true(isinstance(payload, dict), f"artifact valid JSON object: {filename}", errors)
            except Exception as exc:
                assert_true(False, f"artifact parseable JSON: {filename} ({exc})", errors)
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

    coffee_category = str(load_json(coffee_packet / "shoot-plan.json").get("category", ""))
    skin_category = str(load_json(skin_packet / "shoot-plan.json").get("category", ""))
    assert_true(coffee_category != skin_category, "category inference differs across fixtures", errors)


def eval_dry_run_loop(errors: List[str]) -> None:
    packet = run_packet_from_fixture("dry-run-loop", ROOT / "examples" / "scout-samples" / "skincare-serum-scout.json")

    steps = [
        [str(ROOT / "scripts" / "generate-images.py"), "--packet", str(packet)],
        [str(ROOT / "scripts" / "qa-images.py"), "--packet", str(packet)],
        [str(ROOT / "scripts" / "reroll-failed.py"), "--packet", str(packet)],
        [str(ROOT / "scripts" / "export-packager.py"), "--packet", str(packet)],
    ]
    for cmd in steps:
        proc = run(cmd)
        assert_true(proc.returncode == 0, f"command succeeds: {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}", errors)

    gen = packet / "assets" / "generated" / "generation-manifest.json"
    qa = packet / "assets" / "generated" / "qa-results.json"
    reroll = packet / "assets" / "generated" / "reroll-manifest.json"
    exports = sorted((packet / "assets" / "exports").glob("*/export-manifest.json"))

    assert_true(gen.exists(), "generation manifest produced", errors)
    assert_true(qa.exists(), "qa results produced", errors)
    assert_true(reroll.exists(), "reroll manifest produced", errors)
    assert_true(bool(exports), "export manifest produced", errors)

    if reroll.exists():
        reroll_payload = load_json(reroll)
        summary = reroll_payload.get("summary", {})
        assert_true("pass_after_reroll" in summary, "reroll summary has convergence metric", errors)
        assert_true("reroll_exhausted" in summary, "reroll summary has exhaustion metric", errors)


def eval_suite_files(errors: List[str]) -> None:
    required = [
        ROOT / "skills" / "brand-scout" / "SKILL.md",
        ROOT / "skills" / "product-preservation" / "SKILL.md",
        ROOT / "skills" / "visual-gap-audit" / "SKILL.md",
        ROOT / "skills" / "shoot-director" / "SKILL.md",
        ROOT / "skills" / "prompt-factory" / "SKILL.md",
        ROOT / "skills" / "qa-reroll" / "SKILL.md",
        ROOT / "skills" / "export-packager" / "SKILL.md",
        ROOT / "skills" / "memory-writer" / "SKILL.md",
    ]
    for path in required:
        assert_true(path.exists(), f"suite skill exists: {path.relative_to(ROOT)}", errors)


def main() -> int:
    errors: List[str] = []

    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    try:
        eval_artifacts(errors)
        eval_prompt_differentiation(errors)
        eval_dry_run_loop(errors)
        eval_suite_files(errors)
    except Exception as exc:
        print(f"FAIL harness runtime error: {exc}")
        errors.append(f"runtime error: {exc}")

    print(f"\nSummary: {len(errors)} failures")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
