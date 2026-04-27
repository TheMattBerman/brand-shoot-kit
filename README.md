# Brand Shoot Kit

**An end-to-end AI product photography operator for ecommerce brands.**

Give it a product URL. It scouts the page, finds the real product reference, builds a preservation plan, generates a channel-ready shoot, QA-scores every frame, rerolls failures, exports resized assets, and finishes with a polished static frontend at:

```text
<packet>/index.html
```

That page is the magic moment: open one file and see the generated product shoot as a premium review gallery — images first, QA visible, export links ready, provenance included.

```text
URL → Scout → Preserve → Shot Plan → Generate → QA → Reroll → Export → Review Frontend
```

Not a prompt dump. Not an ad-spy workflow. Not “make a pretty product image.”

**A controlled visual production system for ecommerce assets.**

---

## Why This Exists

Ecommerce teams need more product visuals than traditional shoots can reasonably produce:

- PDP heroes
- detail/label shots
- hand-held scale proof
- lifestyle/product-in-use scenes
- email heroes
- social crops
- marketplace-safe assets
- seasonal variants
- bundle/contents layouts

Generic AI is fast, but it breaks the things brands actually care about: package geometry, label text, claims, product count, and brand cues.

Brand Shoot Kit puts product truth first. Every run starts from source-page evidence and a real reference image, then wraps generation in QA, reroll, export, and human review.

---

## Current Proof

Live proofs have already exercised the core categories and failure modes.

| Brand / Category | Result | What was proven |
|---|---:|---|
| **Grüns / supplements** | **12 / 12 live QA pass** | Full ratio-aware 12-shot library with `1:1`, `4:5`, `9:16`, and `16:9` outputs |
| **Rhode / skincare** | **3 / 3 live QA pass** | Reference selection avoided cross-sell drift and preserved primary product fidelity |
| **Blueland / cleaning kit** | **3 / 3 live QA pass** | Multi-product kit references and packaging constraints stayed stable |
| **Stumptown / coffee** | **3 / 3 live QA pass after fix** | Product-reference selection now prefers real product bag imagery and coffee guardrails suppress mug/beans/story-art drift |

The important part: when a category exposed a weakness, the system got better. Stumptown first failed because story art was selected as the reference. The selector now prefers JSON-LD/Shopify product images and coffee prompts enforce bag label/artwork dominance.

---

## The Magic Moment Frontend

Every end-to-end proof run now emits a static showpiece frontend:

```text
<packet>/index.html
```

It is offline-safe, uses relative paths, and can be opened directly in a browser.

The frontend includes:

- premium gallery layout with all generated images front and center
- product/brand/run-status hero
- approve/reroll/reject summary
- filterable image cards
- QA status and weighted scores
- product accuracy / commerce usefulness / brand fit / realism / clarity / artifact-risk breakdown
- requested ratio and final dimensions
- rendered export links by channel
- reference-image panel
- command/provenance summary
- legacy review artifacts preserved under `assets/review/`

This is what you show someone. Not the JSON. Not the terminal output. The frontend.

---

## What the Pipeline Produces

A full packet includes:

| Artifact | Purpose |
|---|---|
| `scout.json` | Product facts, page evidence, source images, structured extraction |
| `preservation.json` | Must-preserve packaging, label, claim, and geometry constraints |
| `visual-gaps.json` | What the current brand gallery is missing |
| `shoot-plan.json` | Category-aware PDP/lifestyle/social/email/marketplace shot plan |
| `prompts.json` | Shot-specific prompts with scale, human, context, and negative constraints |
| `assets/generated/*` | Generated images + generation manifest |
| `assets/generated/qa-results.json` | QA scores, reasons, reroll queue |
| `assets/generated/reroll-manifest.json` | Reroll attempts and final status |
| `assets/exports/**` | Channel-rendered assets with dimensions metadata |
| `assets/review/contact-sheet.html` | Legacy-compatible review dashboard |
| `index.html` | Primary magic-moment frontend |

---

## Quick Start

Validate everything:

```bash
./doctor.sh
./evals/run.py
```

Run no-spend end-to-end mode:

```bash
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out ./output/live-proof-dry/sample \
  --max-shots 3
```

Open:

```text
./output/live-proof-dry/sample/index.html
```

Run a capped live proof:

```bash
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out ./output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry
```

Live mode requires `OPENAI_API_KEY` and explicit `--live-confirm`.

---

## Ratio-Aware Generation

Shots do not just say they are different sizes. They actually render that way.

| Requested Ratio | Final Dimensions |
|---|---:|
| `1:1` | `1024 × 1024` |
| `4:5` | `1024 × 1280` |
| `9:16` | `1080 × 1920` |
| `16:9` | `1920 × 1080` |

Each generation entry records:

- `requested_ratio`
- `provider_size`
- `final_dimensions`
- `postprocess_mode`
- `reference_image_path`
- `reference_image_url`
- `image_sha256`

---

## Reference Selection

Bad references create bad product shots. The selector prefers actual product/package imagery over:

- logos/icons
- nutrition/facts panels
- trust badges
- review graphics
- cross-sell products
- story/tout art
- mug/beans-only coffee context
- accessories or phone cases

For Shopify-style stores, structured JSON-LD/product JSON images get priority because they often contain the cleanest product reference.

Manual override is still available:

```bash
./scripts/generate-images.py \
  --packet <packet-dir> \
  --live \
  --reference-image ./path/to/product.png
```

---

## QA + Reroll Loop

QA scores each frame across:

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

## Export Rendering

Exports are not just copied into folders. They are rendered into channel-ready dimensions with manifest metadata:

- `output_dimensions`
- `render_mode`
- `channel`
- `ratio`
- `source_path`
- `path`

So the frontend can show both the source image and the actual deliverable files.

---

## Category Coverage

Deterministic fixtures/golden runs currently cover:

- coffee
- skincare
- supplements
- cleaning kits

Category logic includes shot taxonomy, preservation constraints, scene hints, negative constraints, and reference-selection guardrails.

---

## Core Commands

| Command | Job |
|---|---|
| `./scripts/run-live-proof.sh` | Full end-to-end proof runner |
| `./scripts/run-brand-shoot.py` | Build packet strategy artifacts |
| `./scripts/generate-images.py` | Generate ratio-aware images |
| `./scripts/qa-images.py` | Score outputs |
| `./scripts/reroll-failed.py` | Reroll failed/manual-review shots |
| `./scripts/export-packager.py` | Render/export channel assets |
| `./scripts/package-review-artifacts.py` | Build `index.html` + review artifacts |
| `./evals/run.py` | Deterministic contract/eval harness |
| `./doctor.sh` | Environment and end-to-end sanity check |

---

## Repo Map

```text
scripts/      pipeline + module entrypoints
references/   rubrics, guidance, module contracts
skills/       skill modules
evals/        deterministic harness and fixtures
examples/     golden runs and sample inputs
output/       generated run packets
```

---

## The Big Idea

The future of ecommerce creative is not one magic prompt.

It is a production loop:

```text
Real product evidence → constrained generation → automated QA → channel exports → human taste → reusable memory
```

Brand Shoot Kit is that loop in repo form.
