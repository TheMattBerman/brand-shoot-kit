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

## Repo Layout

- `SKILL.md`: core behavior contract
- `references/`: deep rubrics and anti-pattern guidance
- `scripts/`: scaffolding + packet generation helpers
- `SUITE.md`: moduleized architecture for productized system evolution
- `evals/`: trigger and execution benchmarks
- `examples/`: practical configs and packet samples
- `output/`: generated artifacts

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
