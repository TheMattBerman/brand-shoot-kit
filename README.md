# Brand Shoot Kit

**An end-to-end AI product photography operator that turns a product URL into a channel-ready shoot, with QA, reroll, exports, and a magic-moment review frontend.**

Built for [OpenClaw](https://openclaw.ai) and [Claude Cowork](https://claude.com/product/cowork) style agent workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with OpenClaw](https://img.shields.io/badge/Built%20with-OpenClaw-blue)](https://openclaw.ai)
[![Works with Claude Cowork](https://img.shields.io/badge/Works%20with-Claude%20Cowork-7c3aed)](https://claude.com/product/cowork)

---

## What It Does

```text
URL → Scout → Preserve → Shot Plan → Generate → QA → Reroll → Export → Review Frontend
```

Give it a product URL. The agent does the rest:

1. **Scouts** the page and extracts product facts, real product imagery, and brand cues
2. **Preserves** what cannot change: package geometry, label text, claim copy, product count
3. **Audits** the visual gaps in the brand's existing gallery
4. **Plans** a 12-shot pack across PDP, lifestyle, social, email, and marketplace
5. **Generates** ratio-aware images at the dimensions the channel actually wants
6. **QA-scores** every frame against a 6-criteria rubric, no vibes
7. **Rerolls** failures with rewritten prompts and the same product reference
8. **Exports** channel-ready assets with manifest metadata
9. **Renders** a static `index.html` review frontend so you can ship the run, not the JSON

Not a prompt dump. Not an ad-spy workflow. Not "make a pretty product image."

**A controlled visual production system for ecommerce assets.**

> 👀 **See the output first:** every run produces `<packet>/index.html` — a premium gallery with images, QA scores, exports, reference, and provenance. Open it in a browser to see what a finished shoot looks like.

---

## Why This Exists

Ecommerce teams need more product visuals than traditional shoots can reasonably produce. PDP heroes, label detail, hand-held scale proof, lifestyle, email heroes, social crops, marketplace-safe assets, seasonal variants, bundle layouts. A single studio day cannot keep up with the visual surface area of a modern brand.

Generic AI is fast, but it breaks the things brands actually care about: package geometry, label text, claims, product count, and brand cues. One round of "make me a hero image" produces a pretty render of a product that does not legally exist.

I built Brand Shoot Kit to put product truth first. Every run starts from source-page evidence and a real product reference image, then wraps generation in QA, reroll, export, and human review. It is the part of the workflow most AI image tools skip: the part that decides what to shoot, what must be preserved, and what counts as good enough to ship.

I'm open-sourcing it because every brand running a real catalog deserves a production loop, not a prompt.

---

## What a Real Run Looks Like

Live proofs across four very different categories, each one used to harden a different failure mode.

| Brand / Category | Result | What was proven |
|---|---:|---|
| **Grüns / supplements** | **12 / 12 live QA pass** | Full ratio-aware 12-shot library across `1:1`, `4:5`, `9:16`, `16:9` |
| **Rhode / skincare** | **3 / 3 live QA pass** | Reference selector avoided cross-sell drift, primary product fidelity preserved |
| **Blueland / cleaning kit** | **3 / 3 live QA pass** | Multi-product kit references and packaging constraints stayed stable |
| **Stumptown / coffee** | **3 / 3 live QA pass after fix** | Selector now prefers JSON-LD/Shopify product imagery, suppresses mug/beans/story-art drift |

The important part: when a category exposed a weakness, the system got better. Stumptown first failed because story art was selected as the reference. The selector now prefers JSON-LD/Shopify product images and coffee prompts enforce bag label/artwork dominance. Each new brand sharpens the kit for the next one.

---

## The Magic Moment Frontend

Every end-to-end run emits a static showpiece frontend at the packet root:

```text
<packet>/index.html
```

Offline-safe. Relative paths. Drop the folder anywhere and the page still works.

It includes:

- premium gallery layout with all generated images front and center
- product, brand, and run-status hero
- approve / reroll / reject summary
- filterable image cards
- QA status with weighted scores
- product accuracy, commerce usefulness, brand fit, realism, clarity, and artifact-risk breakdown per shot
- requested ratio and final dimensions
- rendered export links by channel
- reference-image panel
- command and provenance summary
- legacy review artifacts preserved under `assets/review/`

This is what you show someone. Not the JSON. Not the terminal output. The frontend.

---

## The 8 Skills

Brand Shoot Kit ships as cooperating modules under `skills/`, not one monolithic prompt. Each skill has a deterministic input/output contract and at least one runnable script.

| Skill | What it does |
|-------|--------------|
| `brand-scout` | Pulls product facts, page evidence, source images, and structured extraction from the product URL |
| `product-preservation` | Builds the must-preserve brief: package geometry, label text, claims, product count |
| `visual-gap-audit` | Compares the brand's existing visuals to a healthy ecommerce shot library and prioritizes gaps |
| `shoot-director` | Picks a direction and produces a category-aware 12-shot plan across PDP, lifestyle, social, email, marketplace |
| `prompt-factory` | Turns the shot plan into shot-specific prompts with scale, human, context, and negative constraints |
| `qa-reroll` | Scores each frame against the 6-criteria rubric and reruns failures with rewritten prompts |
| `export-packager` | Renders channel-ready dimensions and writes a manifest the frontend can link from |
| `memory-writer` | Stores what to preserve, avoid, and prefer next time |

Each skill is a plain markdown SKILL.md plus scripts. Any agent framework that reads skills can run this kit.

---

## What the Pipeline Produces

A full packet includes:

| Artifact | Purpose |
|---|---|
| `scout.json` | Product facts, page evidence, source images, structured extraction |
| `preservation.json` | Must-preserve packaging, label, claim, and geometry constraints |
| `visual-gaps.json` | What the current brand gallery is missing |
| `shoot-plan.json` | Category-aware PDP / lifestyle / social / email / marketplace shot plan |
| `prompts.json` | Shot-specific prompts with scale, human, context, and negative constraints |
| `assets/generated/*` | Generated images plus generation manifest |
| `assets/generated/qa-results.json` | QA scores, reasons, and reroll queue |
| `assets/generated/reroll-manifest.json` | Reroll attempts and final status |
| `assets/exports/**` | Channel-rendered assets with dimensions metadata |
| `assets/review/contact-sheet.html` | Legacy-compatible review dashboard |
| `index.html` | Primary magic-moment frontend |

---

## Quick Start

### Prerequisites

- `bash` and `python3`
- (For live mode) `OPENAI_API_KEY`
- (Optional) [OpenClaw](https://openclaw.ai) installed if you want chat / cron / memory around the kit

### 1. Clone and install

```bash
git clone https://github.com/TheMattBerman/brand-shoot-kit.git
cd brand-shoot-kit
./install.sh                     # installs into ~/.clawd/skills/ by default
```

### 2. Validate the environment

```bash
./doctor.sh
./evals/run.py
```

### 3. Run a no-spend dry proof

```bash
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out ./output/live-proof-dry/sample \
  --max-shots 3
```

Open the result:

```text
./output/live-proof-dry/sample/index.html
```

### 4. Run a capped live proof

```bash
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out ./output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry
```

Live mode requires `OPENAI_API_KEY` and explicit `--live-confirm`. Default `--reroll dry` exercises the reroll path without burning extra paid calls.

### 5. Scale to the full 12 shots

Once the 3-shot proof reads cleanly in `index.html`, drop `--max-shots` and run the full pack. See [LIVE-PROOF-PLAYBOOK.md](./LIVE-PROOF-PLAYBOOK.md) for the calibration loop.

---

## Ratio-Aware Generation

Shots do not just say they are different sizes. They actually render that way.

| Requested Ratio | Final Dimensions |
|---|---:|
| `1:1` | `1024 × 1024` |
| `4:5` | `1024 × 1280` |
| `9:16` | `1080 × 1920` |
| `16:9` | `1920 × 1080` |

Each generation entry records `requested_ratio`, `provider_size`, `final_dimensions`, `postprocess_mode`, `reference_image_path`, `reference_image_url`, and `image_sha256` so the frontend can prove what was made and what it was made from.

---

## Reference Selection

Bad references make bad product shots. The selector prefers actual product or package imagery and suppresses:

- logos and icons
- nutrition / facts panels
- trust badges
- review graphics
- cross-sell products
- story / tout art
- mug or beans-only coffee context
- accessories and phone cases

For Shopify-style stores, structured JSON-LD and product JSON images get priority because they often contain the cleanest reference.

Manual override is always available:

```bash
./scripts/generate-images.py \
  --packet <packet-dir> \
  --live \
  --reference-image ./path/to/product.png
```

---

## QA + Reroll Loop

QA scores each frame across six weighted criteria:

| Criterion | Weight |
|---|---:|
| Product accuracy | 30% |
| Commerce usefulness | 20% |
| Brand fit | 15% |
| Scene realism | 15% |
| Visual clarity | 10% |
| Artifact risk | 10% |

Reroll flow:

```text
Fail → Rewrite Prompt → Regenerate With Same Reference → Re-score → Pass or Exhaust
```

The point is not to pretend every AI output is good. The point is to catch failures before a human has to.

---

## Cost Comparison

| The Old Way | The Agent Way |
|-------------|--------------|
| Studio day rental: $2,000 | OpenAI image API: ~$0.10 per shot |
| Photographer: $2,500 | Brand Shoot Kit: free |
| Stylist + props: $1,200 | OpenClaw: free |
| Model + makeup: $1,500 | QA + reroll: built in |
| Retoucher (12 shots): $1,800 | Human review: 10 minutes |
| Reshoot if a shot fails: another $2,000+ | Reroll loop: included |
| Time to deliver: 2-4 weeks | Time to deliver: 30 minutes |
| **One shoot: ~$11,000** | **One full 12-shot packet: ~$1.50** |

A real photo day still wins for hero campaigns. Brand Shoot Kit wins for the other 90% of the visuals a brand actually needs every month.

---

## API Keys and What's Free

| Level | APIs | What Works |
|-------|------|------------|
| **Dry run** | None | Full pipeline, fixtures, golden runs, frontend, no images generated |
| **Live image generation** | `OPENAI_API_KEY` | Real generation, real QA, real exports |
| **Optional scout enrichment** | `FIRECRAWL_API_KEY` | Cleaner page extraction on stubborn sites |
| **Optional alt providers** | `GOOGLE_AI_API_KEY`, `REPLICATE_API_TOKEN` | Drop-in alternatives for image generation |
| **Optional social scouting** | `APIFY_API_TOKEN` | Pull additional brand reference imagery |

See `openclaw.example.json` for the full env shape. Start at $0 with `--dry-run` and the deterministic fixtures, then add `OPENAI_API_KEY` when you want live shots.

---

## Category Coverage

Deterministic fixtures and golden runs currently cover:

- **coffee** — bag label and artwork dominance, no mug/beans drift
- **skincare** — primary product fidelity, no cross-sell drift
- **supplements** — pouch, sachet, gummy, and mixed-format coverage
- **cleaning kits** — multi-product kit references and packaging consistency

Category logic includes shot taxonomy, preservation constraints, scene hints, negative constraints, and reference-selection guardrails. New categories add a fixture, a few rules, and an eval. They do not require touching the pipeline.

---

## Core Commands

| Command | Job |
|---|---|
| `./scripts/run-live-proof.sh` | Full end-to-end proof runner |
| `./scripts/run-brand-shoot.py` | Build packet strategy artifacts |
| `./scripts/generate-images.py` | Generate ratio-aware images |
| `./scripts/qa-images.py` | Score outputs |
| `./scripts/reroll-failed.py` | Reroll failed or manual-review shots |
| `./scripts/export-packager.py` | Render and export channel assets |
| `./scripts/package-review-artifacts.py` | Build `index.html` and review artifacts |
| `./evals/run.py` | Deterministic contract / eval harness |
| `./doctor.sh` | Environment and end-to-end sanity check |

---

## File Structure

```text
brand-shoot-kit/
├── README.md                    # You're here
├── SKILL.md                     # Root orchestrator skill (OpenClaw entrypoint)
├── SUITE.md                     # Module graph and stage contracts
├── SPEC.md                      # Full product spec and build plan
├── LIVE-PROOF-PLAYBOOK.md       # The calibration loop from 3 shots to 12
├── REVIEW.md                    # Review notes and decisions
├── VERSION
├── doctor.sh                    # Environment + sanity check
├── install.sh                   # Install skills into ~/.clawd/skills/
├── uninstall.sh
├── openclaw.example.json
├── skills/                      # ← THE CORE (works with any agent)
│   ├── brand-scout/
│   ├── product-preservation/
│   ├── visual-gap-audit/
│   ├── shoot-director/
│   ├── prompt-factory/
│   ├── qa-reroll/
│   ├── export-packager/
│   └── memory-writer/
├── scripts/                     # Pipeline + module entrypoints
│   ├── run-live-proof.sh
│   ├── run-brand-shoot.py
│   ├── generate-images.py
│   ├── qa-images.py
│   ├── reroll-failed.py
│   ├── export-packager.py
│   ├── package-review-artifacts.py
│   ├── reference_selector.py
│   ├── scout-structured.py
│   └── modules/                 # Per-module owner entrypoints
├── references/                  # Rubrics, guidance, module contracts
├── evals/                       # Deterministic harness and fixtures
├── examples/                    # Golden runs and sample inputs
└── output/                      # Generated run packets (gitignored)
```

---

## Non-Negotiables

Hard rules baked into every stage:

1. **Product truth beats aesthetics.** A pretty image of the wrong package is a failure.
2. **Diagnose before generating.** Scout, preserve, and audit gaps before any prompt is written.
3. **The frontend is the deliverable.** Not the JSON. Not the terminal. The `index.html`.
4. **Live mode is gated.** `--live-confirm` plus `OPENAI_API_KEY` plus capped shot count. No accidental spend.
5. **QA is the gate, not a suggestion.** Failed shots get a reroll, not a pass.
6. **Reference imagery is real or the run does not start.** No story art, no tout art, no logos masquerading as packaging.

---

## The Big Idea

The future of ecommerce creative is not one magic prompt.

It is a production loop:

```text
Real product evidence → constrained generation → automated QA → channel exports → human taste → reusable memory
```

Brand Shoot Kit is that loop in repo form.

---

## More OpenClaw Kits

Run this alongside the rest of the kit set for a full brand and growth loop:

- **[Creator Breakout Kit](https://github.com/TheMattBerman/creator-breakout-kit)** — Strategy layer that finds breakout creator angles, hooks, and concepts before you pay to source or produce
- **[SEO Kit](https://github.com/TheMattBerman/seo-kit)** — AI agent that finds keywords, writes content, builds backlinks, monitors rankings, and self-improves
- **[Outcome Kit](https://github.com/TheMattBerman/outcome-kit)** — Finds fake winners, real winners, and conversion leaks across ads, pages, and outcomes

Brand Shoot Kit feeds the others. The shoot becomes the ad creative, the article hero, the landing page asset, the email, the social post.

---

## License

MIT License. See [LICENSE](LICENSE). Use it, fork it, build on it.

---

## About

Built by [Matt Berman](https://twitter.com/themattberman).

- 🐦 Twitter / X: [@themattberman](https://twitter.com/themattberman)
- 📰 Newsletter: [Big Players](https://bigplayers.co)
- 🏢 Agency: [Emerald Digital](https://emerald.digital)

This is for operators who need a real visual production system, not another prompt.

---

*Star the repo if this helps. It tells me to keep building.*
