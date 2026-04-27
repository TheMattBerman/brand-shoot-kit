# Brand Shoot Kit

Brand Shoot Kit turns a product URL into an ecommerce visual production workflow:
`product URL -> scout.json -> preservation.json -> visual-gaps.json -> shoot-plan.json -> prompts.json -> packet docs -> generation manifest -> QA results -> reroll manifest -> export package`.

This kit is for product photography and ecommerce asset libraries. It is explicitly not an ad spy/ad intelligence workflow.

## What You Get

- Lean behavior-changing [SKILL.md](SKILL.md)
- Suite architecture and module contracts in [SUITE.md](SUITE.md) and `references/module-contracts/`
- Strong reference guides in `references/`
- Runnable scripts in `scripts/`
- First-class module artifacts aligned to `references/module-contracts/*.md`
- Install/doctor/uninstall lifecycle
- Executable eval harness in `evals/run.py` plus trigger/execution docs
- Example shoot packets for multiple product types
- Golden dry-run bundles in `examples/golden-runs/`

## Quick Start

```bash
./doctor.sh
./scripts/run-brand-shoot.py \
  --url "https://example.com/products/hydrating-face-serum" \
  --out ./output/example-skin/hydrating-face-serum/$(date +%F)
```

Offline/no-network smoke flow:

```bash
./scripts/run-smoke.sh
```

Dry-run executable v0.2 flow (no paid API calls):

```bash
./scripts/generate-images.py --packet ./output/example-skin/hydrating-face-serum/$(date +%F)
./scripts/qa-images.py --packet ./output/example-skin/hydrating-face-serum/$(date +%F)
./scripts/reroll-failed.py --packet ./output/example-skin/hydrating-face-serum/$(date +%F)
./scripts/export-packager.py --packet ./output/example-skin/hydrating-face-serum/$(date +%F)
```

Operator-safe live proof runner (default no-spend unless `--live-confirm`):

```bash
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out ./output/live-proof-dry/sample \
  --max-shots 3
```

Live proof (explicit spend gate + API key required):

```bash
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out ./output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry
```

Build deterministic golden run bundles (no-spend):

```bash
./scripts/build-golden-runs.sh
./scripts/build-golden-runs.sh --check
```

Regenerate only one stage artifact:

```bash
./scripts/run-brand-shoot.py --out <packet-dir> --stage prompts
```

Opt-in live generation/vision (requires `OPENAI_API_KEY` and explicit `--live`):

```bash
./scripts/generate-images.py --packet <packet-dir> --live
./scripts/qa-images.py --packet <packet-dir> --live
```

Config-driven fallback:

```bash
./scripts/create-shoot-packet.py \
  --config ./examples/skincare-serum/config.json \
  --out ./output/example-skin/hydrating-serum/$(date +%F)
```

## Graceful Degradation

No API keys required for planning mode.
Without `OPENAI_API_KEY` (or other optional keys), the kit still produces:
- brand analysis
- visual gap audit
- shoot strategy
- shot list
- generation prompts
- deterministic generation manifests + placeholder images
- deterministic/manual QA JSON + markdown report append
- deterministic reroll simulation manifest + QA reroll history append
- deterministic channel export package + export manifest
- operator proof summary (`LIVE_PROOF_SUMMARY.md`) with run commands, artifact status, and go/no-go decisions

## Repo Layout

- `SKILL.md`: core behavior contract
- `references/`: deep rubrics and anti-pattern guidance
- `scripts/`: scaffolding + packet generation helpers
- `SUITE.md`: moduleized architecture for productized system evolution
- `evals/`: trigger and execution benchmarks
- `examples/`: practical configs and packet samples
- `examples/golden-runs/`: deterministic dry-run golden structure bundles
- `output/`: generated artifacts

## Module Entrypoints

Each suite module has an independent executable owner path:

- `scripts/modules/brand_scout.py` -> `scout.json`
- `scripts/modules/product_preservation.py` -> `preservation.json`
- `scripts/modules/visual_gap_audit.py` -> `visual-gaps.json`
- `scripts/modules/shoot_director.py` -> `shoot-plan.json`
- `scripts/modules/prompt_factory.py` -> `prompts.json`
- `scripts/modules/qa_reroll.py` -> `assets/generated/reroll-manifest.json` (and optional QA refresh)
- `scripts/modules/export_packager.py` -> export manifest
- `scripts/modules/memory_writer.py` -> `memory/*.md`

## Install

```bash
./install.sh
```

Options:
- `./install.sh --target "$HOME/.clawd/skills"`
- `./install.sh --dry-run`

## Validate

```bash
./doctor.sh
```

Run executable evals directly:

```bash
./evals/run.py
```

## Uninstall

```bash
./uninstall.sh
```

Removes installed copy only; generated output remains in your workspace.


## Skill Suite

This repo includes the root `brand-shoot-kit` skill plus real module skills in `skills/`:
`brand-scout`, `product-preservation`, `visual-gap-audit`, `shoot-director`, `prompt-factory`, `qa-reroll`, `export-packager`, and `memory-writer`.

Add both the repo root and `skills/` to OpenClaw `extraDirs` if you want the orchestrator and each module independently discoverable.
