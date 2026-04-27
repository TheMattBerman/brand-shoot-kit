# CODEX_RESULT

## Implementation Summary (P1 depth pass)

This pass implemented the requested P1 upgrades as executable code with no-spend defaults.

### 1) Structured scout extraction depth

- Added `scripts/scout_structured.py` (+ executable wrapper `scripts/scout-structured.py`).
- `scripts/run-brand-shoot.py` now enriches all scout inputs (URL fetch or fixture JSON) before writing `scout.json`.
- `scout.json` now includes:
  - `product_name`, `brand_name`
  - `product_type`, `product_category`
  - `price`
  - `variants`
  - `claims_benefits`
  - `ingredients_materials_specs`
  - `visible_packaging_text_candidates`
  - `image_evidence` with source/confidence
  - `field_confidence` per structured field
  - `extraction_warnings`
- Preservation stage now reacts to low-confidence extraction by forcing more conservative variation rules and lower accuracy confidence.

### 2) Subskills as module owners

Added executable module owner entrypoints:

- `scripts/modules/brand_scout.py` -> `scout.json`
- `scripts/modules/product_preservation.py` -> `preservation.json`
- `scripts/modules/visual_gap_audit.py` -> `visual-gaps.json`
- `scripts/modules/shoot_director.py` -> `shoot-plan.json`
- `scripts/modules/prompt_factory.py` -> `prompts.json`
- `scripts/modules/qa_reroll.py` -> QA/reroll updates (`reroll-manifest.json`)
- `scripts/modules/export_packager.py` -> export manifest
- `scripts/modules/memory_writer.py` -> `memory/*.md`

Also updated every `skills/*/SKILL.md` to declare executable path + artifact ownership.

### 3) Golden run bundles (deterministic dry-run structure)

- Added `scripts/build-golden-runs.sh` with:
  - build mode (default)
  - `--check` completeness mode
- Added `examples/golden-runs/` structure with two bundle targets:
  - `skincare-serum`
  - `coffee-roast`
- Each bundle includes fixture input, stage artifacts, packet markdown, generation/QA/reroll manifests, export manifest, and memory files.
- Bundle READMEs explicitly label these as dry-run structural proofs, not live-quality proof.

### 4) Evals, doctor, docs

- Replaced `evals/run.py` with expanded executable checks for:
  - richer structured scout fields
  - module entrypoint execution and artifact ownership
  - dry-run end-to-end loop
  - golden bundle build + completeness
- Updated `doctor.sh` to validate module entrypoints and golden bundle build/check commands.
- Updated docs:
  - `README.md`
  - `SUITE.md`
  - `examples/README.md`
  - `references/module-contracts/*.md` (module owner paths + scout field contract expansion)

## Honest Remaining Gaps

- Structured extraction is still heuristic (text/regex confidence-gated), not OCR/DOM-semantic extraction.
- Live generation + live QA quality remains unproven in this no-spend pass.
- Export packaging remains deterministic copy packaging; channel-specific crop/resize rendering is still not implemented.

## Live Proof Tooling (P2 prep pass)

- Added operator-safe wrapper `scripts/run-live-proof.sh`:
  - requires `--url` and `--out`
  - defaults to no-spend dry mode unless explicit `--live-confirm`
  - hard-gates live calls on `OPENAI_API_KEY`
  - supports `--max-shots` (default `3`) to cap proof spend
  - supports `--reroll off|dry|live` with live rerolls additionally gated
  - runs full stage chain: packet -> generate -> QA -> reroll -> export -> summary
  - writes `LIVE_PROOF_SUMMARY.md` with commands, artifacts, QA/reroll/export counts, and go/no-go prompts
- Added first-run calibration and review artifacts:
  - `references/live-qa-calibration.md`
  - `examples/live-proof-review-template.json`
- Added operator playbook:
  - `LIVE-PROOF-PLAYBOOK.md` with dry-first, live-gated 3-shot flow, and 12-shot expansion decision criteria
- Updated health/eval/docs:
  - `doctor.sh` now checks live-proof script help and executes a cheap dry proof command
  - `evals/run.py` now verifies live-proof script presence/executable/help
  - `README.md` now documents dry and live proof commands

## Product Reference Image Support (live generation)

- `scripts/generate-images.py` now supports:
  - `--reference-image` (local file path or URL)
  - `--auto-reference-image/--no-auto-reference-image`
- Live packet runs can auto-select a safe source image from `scout.json` (`image_evidence` first, then `image_urls`), cache it into `assets/reference-images/`, and pass it as a visual reference to OpenAI.
- OpenAI provider now supports:
  - text-only generation via `POST /v1/images/generations`
  - reference-guided generation via direct multipart `POST /v1/images/edits` with robust fallback between `image[]` and `image` form field conventions.
- `generation-manifest.json` now records:
  - run-level `reference_image_path`, `reference_image_url`, `reference_image_mode`, and notes
  - entry-level `reference_image_path` and `reference_image_url`
- `scripts/run-live-proof.sh` now uses `--auto-reference-image` for live generation calls.
- No-spend defaults remain unchanged (`generate-images.py` still defaults to dry-run placeholders unless `--live` is set).
- Added deterministic no-spend coverage:
  - new fixture `evals/fixtures/reference-product.png`
  - `evals/run.py` check asserting reference metadata + cached file path in dry mode with explicit local reference
  - `doctor.sh` command checks for reference-image manifest metadata
