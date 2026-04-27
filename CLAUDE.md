# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Brand Shoot Kit is an end-to-end AI brand photo shoot operator for ecommerce brands. Give it a product URL. The pipeline scouts the page, builds a preservation brief, plans a 12-shot pack, generates ratio-aware images, QA-scores every frame, rerolls failures, exports channel-ready assets, and renders a static `index.html` review frontend at the packet root.

**Scope:** ecommerce website, PDP, lifestyle, email, organic social, marketplace, and catalog imagery. **Not for paid ads.** Ads are out of scope by design — that lane belongs to StealAds. If a feature request reads as "ad creative" or "ad-spy," push back and route it.

The shareable artifact is **the packet**, specifically `<packet>/index.html` — a premium gallery with images, QA scores, exports, reference image, and provenance. Not the JSON. Not the terminal output. The frontend.

Internally, it's a Python + bash + prompt package: no app, no server, no build step. Just a pipeline of deterministic scripts, module-owner entrypoints, skill prompt modules, and golden-run fixtures stitched together via a shared packet directory.

One run = one packet directory under `output/`. Every stage reads and writes files in that directory. Do not introduce global state or cross-run coupling.

## Common commands

```bash
# Environment + sanity check
./doctor.sh

# Deterministic eval harness (no spend, no API)
./evals/run.py

# No-spend dry proof end-to-end
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out ./output/live-proof-dry/sample \
  --max-shots 3

# Capped live proof (requires OPENAI_API_KEY)
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out ./output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry

# Build / check golden run bundles
./scripts/build-golden-runs.sh
```

There is no linter, formatter, or package manager. Scripts use bash plus Python 3 stdlib, with optional HTTP calls inside adapters. Do not add `requirements.txt`, `pyproject.toml`, or framework dependencies without discussing first.

## Pipeline architecture

The end-to-end flow moves through nine stages that share one packet directory:

```text
URL → Scout → Preserve → Gap Audit → Shot Plan → Generate → QA → Reroll → Export → Review Frontend
```

Stage-by-stage:

1. **Scout** (`scripts/scout-structured.py`, `scripts/modules/brand_scout.py`) writes `scout.json` — product facts, page evidence, source images, structured extraction. This is the only stage allowed to read the live URL.
2. **Preserve** (`scripts/modules/product_preservation.py`) writes `preservation.json` — must-preserve packaging, label, claim, and geometry constraints.
3. **Gap audit** (`scripts/modules/visual_gap_audit.py`) writes `visual-gaps.json` — what the brand's existing gallery is missing, prioritized.
4. **Shot plan** (`scripts/modules/shoot_director.py`) writes `shoot-plan.json` — category-aware PDP / lifestyle / social / email / marketplace shot plan.
5. **Prompt factory** (`scripts/modules/prompt_factory.py`) writes `prompts.json` — shot-specific prompts with scale, human, context, and negative constraints.
6. **Generate** (`scripts/generate-images.py`) writes `assets/generated/*` plus a generation manifest. Dry-run by default. Live mode requires `OPENAI_API_KEY` and explicit `--live` (or `--live-confirm` via the proof runner).
7. **QA** (`scripts/qa-images.py`) writes `assets/generated/qa-results.json` — six-criteria weighted scores plus reroll queue. Deterministic scoring by default, optional OpenAI vision mode.
8. **Reroll** (`scripts/reroll-failed.py`) writes `assets/generated/reroll-manifest.json` — rerun failed shots with rewritten prompts and the same product reference. Default `--reroll dry` exercises the path without burning paid calls.
9. **Export** (`scripts/export-packager.py`) writes `assets/exports/**` plus dimensions metadata.
10. **Review frontend** (`scripts/package-review-artifacts.py`) writes `index.html` plus the legacy `assets/review/contact-sheet.html`.

Two orchestrators sit on top:

- **`scripts/run-brand-shoot.py`** is the suite orchestrator. It drives the strategy stages (scout → prompts) and writes the packet artifacts.
- **`scripts/run-live-proof.sh`** is the end-to-end proof runner. It chains the suite orchestrator with generate, QA, reroll, export, and review packaging, and gates live spend behind `--live-confirm`.

Each stage must complete before the next begins. Artifacts are first-class — downstream stages read them, they do not re-derive upstream state.

## Modules vs skills

The same eight modules show up in two places, intentionally:

- **`scripts/modules/<name>.py`** are the deterministic Python module-owner entrypoints. They are where the actual logic lives. Imported by `run-brand-shoot.py` and runnable standalone.
- **`skills/<name>/SKILL.md`** are the prompt modules consumed by an agent (OpenClaw, Claude Code, Cowork). They reference the module scripts by relative path and carry trigger descriptions plus behavior contracts.

The eight modules are: `brand-scout`, `product-preservation`, `visual-gap-audit`, `shoot-director`, `prompt-factory`, `qa-reroll`, `export-packager`, `memory-writer`. The root `SKILL.md` is the orchestrator. Subskills are narrower.

When editing a skill, preserve its YAML frontmatter and the input/output contract under `references/module-contracts/`. Other skills and `run-brand-shoot.py` assume those field names.

## Packet conventions

A packet is one run, one directory. Stage artifacts live at the packet root. Generated images, QA, reroll, exports, and review artifacts live under `assets/`.

```text
<packet>/
├── scout.json
├── preservation.json
├── visual-gaps.json
├── shoot-plan.json
├── prompts.json
├── 00-brand-analysis.md
├── 01-visual-gap-audit.md
├── 02-shoot-strategy.md
├── 03-shot-list.md
├── 04-generation-prompts.md
├── 05-qa-report.md
├── 06-export-map.md
├── index.html                 ← magic-moment frontend
└── assets/
    ├── generated/
    │   ├── *.png
    │   ├── generation-manifest.json
    │   ├── qa-results.json
    │   └── reroll-manifest.json
    ├── exports/
    │   └── <channel>/...
    └── review/
        └── contact-sheet.html
```

`output/` is gitignored. Never commit run output. Never hardcode a specific local packet path into scripts or tests.

## Live spend gates (non-negotiable)

These exist so a single typo cannot accidentally bill a customer's API key.

- **Generation is dry-run by default.** Live mode requires `--live` on `generate-images.py` or `--live-confirm` on `run-live-proof.sh`.
- **`run-live-proof.sh` requires both `--live-confirm` and `OPENAI_API_KEY`.** Missing either one fails fast.
- **`--max-shots` defaults to a small number for proofs.** Scaling to 12 shots is a deliberate choice after a 3-shot proof reads cleanly.
- **Reroll is dry by default.** Use `--reroll live` only when you intentionally approve live reroll spend.
- **Live reroll is gated and unproven by default.** Treat it as experimental until calibration data says otherwise.

If you add a new stage that can spend money, follow the same pattern: dry by default, explicit live flag, fail fast on missing keys.

## Evidence rules (non-negotiable)

These are product constraints, not style preferences. Violating them breaks the kit's core positioning around product truth.

- **Reference imagery is real product imagery or the run does not start.** The reference selector prefers JSON-LD / Shopify product images and suppresses logos, nutrition panels, trust badges, review graphics, cross-sells, story / tout art, mug-or-beans-only coffee context, and accessories. If no real reference is available, surface that — do not fabricate.
- **Generated images record their provenance.** Each generation entry must include `requested_ratio`, `provider_size`, `final_dimensions`, `postprocess_mode`, `reference_image_path`, `reference_image_url`, and `image_sha256`. The frontend reads these to prove what was made and what it was made from.
- **QA is the gate, not a suggestion.** Failures route to the reroll queue. Do not pass shots that fail the rubric just because the run is "almost done."
- **Category guardrails travel with the prompt.** Coffee prompts enforce bag label / artwork dominance. Skincare prompts protect primary product fidelity. Supplements cover pouch / sachet / gummy formats. Cleaning kits preserve multi-product packaging consistency. New categories add a fixture, a few rules, and an eval — they do not touch the pipeline.
- **The frontend is the deliverable.** If `index.html` does not exist or does not render the run cleanly, the packet is not done.

## Adapters and integrations

External services (OpenAI Images, Firecrawl, Google AI, Replicate, Apify) are accessed through narrow adapters. Adapters fetch, normalize, and write JSON — no strategic reasoning. Keep them runnable standalone.

Env shape lives in `openclaw.example.json`. Required for live: `OPENAI_API_KEY`. Optional: `FIRECRAWL_API_KEY`, `GOOGLE_AI_API_KEY`, `REPLICATE_API_TOKEN`, `APIFY_API_TOKEN`.

## Testing

The eval harness is `./evals/run.py`. It exercises the full pipeline against deterministic fixtures and golden runs under `examples/golden-runs/` and `evals/fixtures/`. There is no pytest.

Add coverage when you change a module:

- new shot taxonomy → add a fixture under `evals/fixtures/`
- new category guardrail → extend the relevant golden run
- new stage artifact → update `references/module-contracts/`

Eval failures should be loud. The harness is the only thing standing between a code change and a regressed live shoot.

## Public-release bar

This package is intended to be cloneable by an operator with no prior context. Before changes land, verify:

- `openclaw.example.json` lists every env key referenced by adapters, with no private defaults.
- `./doctor.sh` reports cleanly on a fresh clone.
- `./evals/run.py` passes against the committed fixtures and golden runs.
- The README dry-proof path runs end-to-end without `OPENAI_API_KEY`.
- `index.html` renders correctly from the dry-proof packet.
