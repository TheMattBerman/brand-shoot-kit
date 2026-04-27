# Brand Shoot Kit

Brand Shoot Kit turns a product URL into a full ecommerce visual production system:
`product URL -> brand analysis -> visual gap audit -> shoot strategy -> shot list -> GPT Image-ready prompts -> QA rubric -> export map`.

This kit is for product photography and ecommerce asset libraries. It is explicitly not an ad spy/ad intelligence workflow.

## What You Get

- Lean behavior-changing [SKILL.md](SKILL.md)
- Strong reference guides in `references/`
- Runnable scripts in `scripts/`
- Install/doctor/uninstall lifecycle
- Eval suites for trigger and execution quality
- Example shoot packets for multiple product types

## Quick Start

```bash
./doctor.sh
./scripts/scaffold-output.sh --brand "Example Skin" --product "Hydrating Serum"
./scripts/create-shoot-packet.py \
  --config ./examples/skincare-serum/config.json \
  --out ./output/example-skin/hydrating-serum/$(date +%F)
```

Then run your agent with this repo loaded and pass the product URL plus output path.

## Graceful Degradation

No API keys required for planning mode.
Without `OPENAI_API_KEY` (or other optional keys), the kit still produces:
- brand analysis
- visual gap audit
- shoot strategy
- shot list
- generation prompts
- QA template/rubric
- export map

## Repo Layout

- `SKILL.md`: core behavior contract
- `references/`: deep rubrics and anti-pattern guidance
- `scripts/`: scaffolding + packet generation helpers
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

## Uninstall

```bash
./uninstall.sh
```

Removes installed copy only; generated output remains in your workspace.
