# CODEX_RESULT

## Implementation Summary (P0 executable depth)

This pass implemented the requested P0 improvements as executable code, not review notes.

### 1) Real module artifact pipeline

Implemented first-class stage artifacts in packet root:
- `scout.json`
- `preservation.json`
- `visual-gaps.json`
- `shoot-plan.json`
- `prompts.json`

Key changes:
- `scripts/run-brand-shoot.py`
  - now orchestrates explicit stage pipeline and writes artifacts
  - supports independent stage regeneration via `--stage`:
    - `scout`, `preservation`, `visual-gaps`, `shoot-plan`, `prompts`, `render`, `all`
- `scripts/pipeline_stages.py` (new)
  - shared stage logic and packet markdown rendering
- `scripts/create-shoot-packet.py`
  - now renders docs from artifacts (`--artifacts-dir`) and keeps `--config` compatibility
- `scripts/validate-packet.py`
  - now validates required artifact JSON files too

### 2) Automatic reroll executor

Added `scripts/reroll-failed.py`:
- reads:
  - `assets/generated/qa-results.json`
  - `assets/generated/generation-manifest.json`
  - `prompts.json` (fallback `04-generation-prompts.md`)
- dry-run mode (default):
  - deterministic reroll simulation
  - tracks per-attempt revised prompt, reasons, status
  - writes `assets/generated/reroll-manifest.json`
  - appends reroll history to `05-qa-report.md`
- live mode (`--live`):
  - explicitly gated
  - can call `generate-images.py --live` for selected asset IDs

Related updates:
- `scripts/generate-images.py`
  - added `--asset-ids` filter
  - added `--prompt-overrides` for reroll prompt rewrites
- `scripts/qa-images.py`
  - now includes `reroll_queue` in `qa-results.json`

### 3) Executable eval harness

Added `evals/run.py` + fixture `evals/fixtures/scout-coffee.json`.

Coverage includes:
- module artifacts produced and valid JSON
- cross-category prompt differentiation (non-clone behavior)
- dry-run generation -> QA -> reroll -> export end-to-end
- required suite skill files present

Harness exits non-zero on failure.

### 4) Quality/docs/ops updates

- `scripts/run-smoke.sh`
  - now includes reroll step and verifies reroll manifest
- `doctor.sh`
  - now checks `evals/run.py`, `scripts/reroll-failed.py`
  - now executes `./evals/run.py`
- updated docs:
  - `README.md`
  - `SUITE.md`
- `.gitignore`
  - keeps eval temp junk and pycache out (`evals/.tmp/`, `__pycache__`, `*.pyc`, `output/`)

## Honest Remaining Gaps

- Live generation/vision/reroll quality is still unproven by default; this pass stayed no-spend.
- Structured high-fidelity extraction for variants/claims/spec text is still basic.
- Export stage is still deterministic copy packaging (no crop/resize rendering variants yet).
