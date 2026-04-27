# Brand Shoot Kit

**An AI product photography operator that turns a product URL into a reference-guided ecommerce shoot, QA pass, reroll loop, and review-ready asset pack.**

Brand Shoot Kit is built for the moment every ecommerce brand hits: you need more product shots than a human team can reasonably produce, but generic AI images destroy the packaging, invent label text, and make everything look like plastic slop.

This kit does the opposite.

It starts from the real product page, pulls the real product imagery, builds a preservation plan, generates new shots with a visual reference, scores the outputs, rerolls failures, exports channel-ready assets, and packages everything for human review.

```text
Product URL → Scout → Preservation Plan → Shot Plan → Reference-Guided Generation → QA → Reroll → Export → Review Pack
```

Not an ad spy tool. Not a prompt dump. Not “make me a pretty product image.”

**A controlled visual production loop for ecommerce assets.**

---

## What It Does

Brand Shoot Kit turns one product URL into a full shoot packet:

1. **Scouts the product page** — title, product name, claims, packaging text, image evidence, visual cues
2. **Selects a real product reference image** — avoids logos, icons, nutrition panels, cross-sell images, and other bad inputs
3. **Builds preservation constraints** — what must stay true: package shape, label, brand mark, count, required claims
4. **Plans the shot library** — PDP, lifestyle, model, email, social, marketplace, seasonal
5. **Generates images with ratio-aware sizing** — each shot honors `1:1`, `4:5`, `9:16`, or `16:9` with provider-size mapping plus deterministic output dimensions
6. **Scores the outputs with vision QA** — product accuracy, commerce usefulness, brand fit, realism, clarity, artifact risk
7. **Rerolls failures** — failed QA can trigger prompt rewrite → regenerate with the same reference → re-score
8. **Exports assets by channel** — deterministic package structure for PDP, social, email, marketplace, etc.
9. **Creates a human review pack** — JSON review template, HTML contact sheet, approve/reroll/reject summary

The point is simple: **more ecommerce visuals without losing product fidelity.**

---

## Why This Exists

Ecommerce teams are drowning in visual demand.

Every product needs:

- clean PDP shots
- angle/detail shots
- lifestyle context
- model/hand scale
- email hero images
- social crops
- seasonal variants
- marketplace-safe white-ground shots

Traditional shoots are expensive and slow. Generic AI generation is fast but unreliable. It changes logos, mangles labels, invents claims, adds weird props, and quietly breaks compliance.

Brand Shoot Kit is built around one belief:

> AI product photography is only useful if product preservation is the system’s first-class job.

So the kit does not just ask an image model to imagine a package from text. It gives the model a real visual reference, tracks where that reference came from, scores the output, and forces every image through a QA/review loop.

That’s the difference between a toy demo and a production workflow.

---

## The Pipeline

```text
SCOUT → PRESERVE → AUDIT → DIRECT → PROMPT → GENERATE → QA → REROLL → EXPORT → REVIEW
```

| Stage | Artifact | What It Means |
|---|---|---|
| Scout | `scout.json` | Product facts, page evidence, claims, image URLs |
| Preserve | `preservation.json` | Must-preserve product and label constraints |
| Gap Audit | `visual-gaps.json` | What the brand is missing visually |
| Shoot Direction | `shoot-plan.json` | Shot strategy by channel and use case |
| Prompt Factory | `prompts.json` + `04-generation-prompts.md` | Generation prompts with shot-specific scale/human/context guidance + negative constraints |
| Generate | `assets/generated/generation-manifest.json` | Image outputs, ratio metadata (`requested_ratio`, `provider_size`, `final_dimensions`), model, reference path, endpoint |
| QA | `assets/generated/qa-results.json` | Vision/manual QA scores and failure reasons |
| Reroll | `assets/generated/reroll-manifest.json` | Reroll attempts and convergence status |
| Export | `assets/exports/**/export-manifest.json` | Channel-packaged final files |
| Review | `assets/review/*` | Human review template + contact sheet |

Every stage writes an artifact. No hidden vibes. No “trust me bro.”

---

## Proof From Live Tests

The current live proof pass used `gpt-image-2` with real product reference images.

| Brand / Category | Result | Notes |
|---|---:|---|
| Grüns / supplement gummies | **12 / 12 QA pass** | Full 12-shot proof with review pack |
| Rhode / skincare lip treatment | **3 / 3 QA pass** | Fixed reference picker to avoid cross-sell/lip-case images |
| Blueland / cleaning kit | **3 / 3 QA pass** | Fixed category/reference selection for multi-product kits |
| Stumptown / coffee | **2 / 3 QA pass** | Useful failure: coffee-specific prompt/reference nuance still needs tightening |

This is the right kind of failure profile: the system works, and the misses are specific enough to improve.

---

## Quick Start

### 1. Validate the kit

```bash
./doctor.sh
./evals/run.py
```

### 2. Build a no-spend packet from a product URL

```bash
./scripts/run-brand-shoot.py \
  --url "https://example.com/products/sample" \
  --out ./output/sample/$(date +%F)
```

This produces strategy, shot planning, prompts, and deterministic scaffolding without live generation spend.

### 3. Run a safe dry proof

```bash
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out ./output/live-proof-dry/sample \
  --max-shots 3
```

Dry mode creates the full artifact structure with placeholder images. No paid API calls.

### 4. Run a capped live proof

```bash
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out ./output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry
```

Live mode requires `OPENAI_API_KEY`. It is explicit on purpose.

---

## Live Generation: How It Actually Works

Brand Shoot Kit calls OpenAI directly.

| Task | Provider | Endpoint |
|---|---|---|
| Text-only generation fallback | OpenAI | `POST /v1/images/generations` |
| Reference-guided product generation | OpenAI | `POST /v1/images/edits` |
| Vision QA | OpenAI | `POST /v1/responses` |

Default live image model: **`gpt-image-2`**

`scripts/generate-images.py` defaults to `--size auto` so shot ratios map to provider sizes and deterministic final dimensions.

Live packet runs auto-select a reference image from `scout.json`, cache it into:

```text
assets/reference-images/
```

Then each generated asset records:

- `reference_image_url`
- `reference_image_path`
- `openai_image_endpoint`
- `model`
- `image_sha256`
- `requested_ratio`
- `provider_size`
- `final_dimensions`

So you can always see what the model saw and how the output was produced.

---

## Reference Image Selection

Bad reference images create bad product shots.

The kit scores source images and strongly prefers actual package/product imagery over:

- logos
- SVG icons
- nutrition/facts panels
- review graphics
- trust badges
- cross-sell products
- phone cases/accessories
- tiny thumbnails when better product imagery exists

The selector lives in:

```text
scripts/reference_selector.py
```

It uses product-name tokens, ecommerce filename patterns, confidence/rank, URL safety checks, and category heuristics to choose the safest reference.

You can override it manually:

```bash
./scripts/generate-images.py \
  --packet <packet-dir> \
  --live \
  --reference-image ./path/to/product.png
```

Or let it auto-select:

```bash
./scripts/generate-images.py \
  --packet <packet-dir> \
  --live \
  --auto-reference-image
```

---

## QA and Reroll Loop

QA scores each generated image across:

| Criterion | Weight |
|---|---:|
| Product accuracy | 30% |
| Commerce usefulness | 20% |
| Brand fit | 15% |
| Scene realism | 15% |
| Visual clarity | 10% |
| Artifact risk | 10% |

If an image fails, live reroll can now close the loop:

```bash
./scripts/reroll-failed.py \
  --packet <packet-dir> \
  --live \
  --live-qa \
  --qa-threshold 80 \
  --max-attempts 1
```

That means:

```text
Fail → Rewrite Prompt → Regenerate With Same Product Reference → Re-score → Pass or Exhaust
```

No fake “reroll complete” flags. It actually regenerates and rechecks.

---

## Human Review Pack

After export, the kit creates review artifacts in:

```text
assets/review/
```

| File | Purpose |
|---|---|
| `human-review-template.json` | Fillable approve/reroll/reject review sheet |
| `contact-sheet.html` | Visual gallery for fast human review |
| `artifact-pack-manifest.json` | Asset list, QA status, suggested decision counts |

Generate manually:

```bash
./scripts/package-review-artifacts.py --packet <packet-dir>
```

This is where Matt-eye comes in. Model QA catches obvious issues. Human review decides what is actually good enough for a brand.

---

## No-Spend Mode

The kit is safe by default.

Without live flags/API keys, it still produces:

- brand analysis
- visual gap audit
- shoot strategy
- shot list
- generation prompts
- placeholder image manifests
- deterministic/manual QA
- simulated reroll manifest
- export package
- review pack
- `LIVE_PROOF_SUMMARY.md`

Paid/live calls require explicit flags like `--live`, `--live-confirm`, or `--reroll live`.

---

## Install

```bash
./install.sh
```

Options:

```bash
./install.sh --target "$HOME/.clawd/skills"
./install.sh --dry-run
```

Validate:

```bash
./doctor.sh
./evals/run.py
```

Uninstall installed copies only:

```bash
./uninstall.sh
```

Generated output remains in your workspace.

---

## Repo Structure

```text
brand-shoot-kit/
├── README.md
├── SKILL.md
├── SUITE.md
├── LIVE-PROOF-PLAYBOOK.md
├── CODEX_RESULT.md
├── install.sh
├── doctor.sh
├── uninstall.sh
├── references/
├── skills/
│   ├── brand-scout/
│   ├── product-preservation/
│   ├── visual-gap-audit/
│   ├── shoot-director/
│   ├── prompt-factory/
│   ├── qa-reroll/
│   ├── export-packager/
│   └── memory-writer/
├── scripts/
│   ├── run-brand-shoot.py
│   ├── generate-images.py
│   ├── qa-images.py
│   ├── reroll-failed.py
│   ├── export-packager.py
│   ├── package-review-artifacts.py
│   └── reference_selector.py
├── evals/
├── examples/
└── output/
```

---

## Module Entrypoints

Each suite module owns an executable artifact path:

| Module | Script | Owns |
|---|---|---|
| Brand Scout | `scripts/modules/brand_scout.py` | `scout.json` |
| Product Preservation | `scripts/modules/product_preservation.py` | `preservation.json` |
| Visual Gap Audit | `scripts/modules/visual_gap_audit.py` | `visual-gaps.json` |
| Shoot Director | `scripts/modules/shoot_director.py` | `shoot-plan.json` |
| Prompt Factory | `scripts/modules/prompt_factory.py` | `prompts.json` |
| QA / Reroll | `scripts/modules/qa_reroll.py` | QA + reroll manifests |
| Export Packager | `scripts/modules/export_packager.py` | export manifests |
| Memory Writer | `scripts/modules/memory_writer.py` | `memory/*.md` |

---

## What Still Needs Work

This is production-shaped, but not done forever.

Known next improvements:

1. **Coffee-specific prompt refinement** — Stumptown exposed that coffee bag scenes need tighter label/artwork preservation.
2. **Better PDP extraction** — price, variants, ingredients/specs, and packaging text still depend on heuristic HTML extraction unless richer extraction is configured.
3. **Contact sheet polish** — the review HTML works, but could become a slicker operator dashboard.
4. **Channel crop/rendering** — export packaging is deterministic file organization, not true crop/resize rendering yet.
5. **More category baselines** — beauty, supplement, cleaning, coffee are started; more products will sharpen the heuristics.

---

## The Big Idea

The future of ecommerce creative is not “generate one magic image.”

It is a system:

```text
Real product evidence → constrained generation → automated QA → human taste → reusable memory
```

Brand Shoot Kit is that system in repo form.
