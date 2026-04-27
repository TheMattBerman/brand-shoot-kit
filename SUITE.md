# Brand Shoot Kit Suite Architecture (v0)

Brand Shoot Kit should operate as a suite of cooperating modules, not a single monolith prompt.

## Why a Suite

A single skill can describe workflow quality, but production quality needs module boundaries:
- URL/page scouting and evidence extraction
- preservation and risk gating
- gap analysis and prioritization
- shot strategy and prompt generation
- QA reroll loop and export packaging

Without module boundaries, output quality drifts and the system cannot be tested stage by stage.

## Module Graph

1. `brand-scout`
   Input: product URL (+ optional extra brand/social URLs)
   Output: `scout.json` evidence bundle
2. `product-preservation`
   Input: `scout.json`
   Output: preservation brief + distortion risk profile
3. `visual-gap-audit`
   Input: scout + preservation brief
   Output: prioritized gap table
4. `shoot-director`
   Input: gap table + channel goals
   Output: direction choice + 12-shot plan
5. `prompt-factory`
   Input: shot plan + preservation rules
   Output: operational prompts + reroll instructions
6. `qa-reroll`
   Input: generated assets + rubric
   Output: pass/fail report + reroll queue
7. `export-packager`
   Input: approved assets + channel map
   Output: export map + package manifest
8. `memory-writer`
   Input: final packet + QA outcomes
   Output: memory artifacts for next run

Current first-class stage artifacts in packet root:
- `scout.json`
- `preservation.json`
- `visual-gaps.json`
- `shoot-plan.json`
- `prompts.json`

## Implementation Status (April 27, 2026)

- Implemented now:
  - `brand-scout` with deterministic structured enrichment (`scripts/scout-structured.py`, `scripts/modules/brand_scout.py`)
  - `suite-orchestrator` (`scripts/run-brand-shoot.py`) that writes stage artifacts and renders docs
  - module-owner entrypoints for all 8 modules under `scripts/modules/`
  - packet generation + structure validation (`create-shoot-packet.py`, `validate-packet.py`)
  - generation stage with dry-run + optional OpenAI live mode (`scripts/generate-images.py`)
  - QA stage with deterministic/manual scoring + optional OpenAI vision mode (`scripts/qa-images.py`)
  - reroll stage with deterministic dry-run simulation + optional live execution (`scripts/reroll-failed.py`)
  - deterministic export packaging and manifests (`scripts/export-packager.py`)
  - deterministic golden run bundles + builder/check script (`scripts/build-golden-runs.sh`, `examples/golden-runs/`)
- Partial:
  - preservation/gap/strategy remain heuristic/template-driven
  - prompt generation is now category-aware but still rule-based, not model-directed
  - live reroll loop is only partially implemented (gated and unproven by default)
  - structured extraction is heuristic and confidence-gated, not OCR/DOM-semantic grade
- Missing:
  - crop/resize variant rendering per channel (current export is deterministic copy packaging)

## Contract Files

See `references/module-contracts/` for first-pass input/output contracts per module.

## Acceptance Direction

This suite is "actually good" only when each module has:
- deterministic input/output artifacts
- at least one script or executable path
- eval coverage for failure cases
- rerun-safe behavior and memory handoff


## Actual Skill Directories

The suite now includes real OpenClaw skill folders under `skills/`:

- `skills/brand-scout/`
- `skills/product-preservation/`
- `skills/visual-gap-audit/`
- `skills/shoot-director/`
- `skills/prompt-factory/`
- `skills/qa-reroll/`
- `skills/export-packager/`
- `skills/memory-writer/`

The root `brand-shoot-kit` skill orchestrates the full workflow. The subskills are narrower modules with their own trigger descriptions and behavior contracts.
