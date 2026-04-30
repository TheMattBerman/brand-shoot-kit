# AGENTS.md — Brand Shoot Kit

Brand Shoot Kit is a production system for ecommerce brand photo shoots, not a prompt generator.

**Scope:** website, PDP, lifestyle, email, organic social, marketplace, and catalog imagery. **Out of scope:** paid ad creative, ad-spy, competitive ad intelligence. Those belong to StealAds. Keep the lanes clean.

## Mission

Help an operator answer four questions for any product URL:

1. What does this brand actually look like, and what must never change about the product?
2. What visuals is the brand missing across PDP, lifestyle, social, email, and marketplace?
3. Did the AI render those visuals at production quality, or did it drift?
4. What ships, what reruns, and what gets exported where?

## Core Rules

- **Product truth beats aesthetics.** A pretty image of the wrong package is a failure.
- **Diagnose before generating.** Scout, preserve, and audit gaps before any prompt is written.
- **Real references only.** No story art, no tout art, no logos masquerading as packaging.
- **QA is the gate, not a suggestion.** Failed shots reroll, they do not ship.
- **Live spend is always gated.** Dry by default. Explicit confirm. Fail fast on missing keys.
- **The frontend is the deliverable.** `<packet>/index.html`. Not the JSON. Not the terminal.

## Tone

Sharp, clear, operator-grade.
No prompt-engineering theater.
No "AI can do photography now" hand-waving.

## Default Output Shape

Every end-to-end run produces:

- `index.html` — magic-moment frontend
- 12 generated shots across `1:1`, `4:5`, `9:16`, `16:9`
- six-criteria QA scores per shot
- channel-rendered exports with dimensions metadata
- reference image, prompts, and provenance preserved alongside

## Pipeline Order

```text
SCOUT → PRESERVE → GAP AUDIT → SHOT PLAN → PROMPTS → GENERATE → QA → REROLL → EXPORT → REVIEW FRONTEND
```

Each stage must complete before the next begins. Artifacts flow through the packet directory under `output/`.

## The 8 Skills

### skills/brand-scout — Page Evidence

**Purpose:** Pull product facts, page evidence, source images, and structured extraction from a product URL.
**Scripts:** `scripts/scout-structured.py`, `scripts/modules/brand_scout.py`
**Data Sources:** Dispatched between `scripts/adapters/curl_scrape.py` (regex over `curl`-fetched HTML) and `scripts/adapters/firecrawl_scrape.py` (Firecrawl `/v2/scrape` with JSON-schema extraction). Selection follows `--scraper` flag → `BSK_FORCE_SCRAPER` env → `FIRECRAWL_API_KEY` env → curl default. Output adds a top-level `scrape_provenance` object recording which adapter ran.
**Output:** `scout.json` (with `scrape_provenance`) plus `00-brand-analysis.md`.
**Mode:** Deterministic, confidence-gated.

### skills/product-preservation — Must-Preserve Brief

**Purpose:** Identify what cannot change. Package geometry, label text, claim copy, product count, brand cues.
**Scripts:** `scripts/modules/product_preservation.py`
**Output:** `preservation.json`.
**Mode:** Heuristic and template-driven (partial). Drives downstream prompt constraints and reroll instructions.

### skills/visual-gap-audit — Gap Prioritization

**Purpose:** Compare the brand's existing gallery to a healthy ecommerce shot library. Surface what is missing and rank it.
**Scripts:** `scripts/modules/visual_gap_audit.py`
**Output:** `visual-gaps.json` plus `01-visual-gap-audit.md`.

### skills/shoot-director — Direction + Shot Plan

**Purpose:** Pick a direction with rationale. Produce a category-aware 12-shot plan across PDP, lifestyle, social, email, marketplace.
**Scripts:** `scripts/modules/shoot_director.py`
**Output:** `shoot-plan.json` plus `02-shoot-strategy.md` and `03-shot-list.md`.
**Categories covered:** coffee, skincare, supplements, cleaning kits.

### skills/prompt-factory — Prompts + Negatives

**Purpose:** Turn the shot plan into shot-specific prompts with scale, human, context, and negative constraints. Ratio-aware.
**Scripts:** `scripts/modules/prompt_factory.py`
**Output:** `prompts.json` plus `04-generation-prompts.md`.
**Mode:** Category-aware rule-based, not model-directed.

### skills/qa-reroll — Score + Rerun

**Purpose:** Score each frame against the six-criteria rubric. Rerun failures with rewritten prompts and the same product reference.
**Scripts:** `scripts/qa-images.py`, `scripts/reroll-failed.py`, `scripts/modules/qa_reroll.py`
**Output:** `assets/generated/qa-results.json`, `assets/generated/reroll-manifest.json`, `05-qa-report.md`.
**Mode:** Deterministic scoring by default, optional OpenAI vision mode for live runs.

### skills/export-packager — Channel Renders

**Purpose:** Render channel-ready dimensions. Write a manifest the frontend can link from.
**Scripts:** `scripts/export-packager.py`, `scripts/modules/export_packager.py`
**Output:** `assets/exports/**` plus `06-export-map.md`.
**Manifest fields per export:** `output_dimensions`, `render_mode`, `channel`, `ratio`, `source_path`, `path`.

### skills/memory-writer — Reusable Memory

**Purpose:** Store what to preserve, avoid, and prefer next run. Compounds across runs and brands.
**Scripts:** `scripts/modules/memory_writer.py`
**Output:** Memory artifacts written alongside the packet.

## Ratio-Aware Generation

Shots do not just say they are different sizes. They actually render that way.

| Requested Ratio | Final Dimensions |
|---|---:|
| `1:1` | `1024 × 1024` |
| `4:5` | `1024 × 1280` |
| `9:16` | `1080 × 1920` |
| `16:9` | `1920 × 1080` |

## QA Rubric

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

## Reference Selection Rules

The selector prefers actual product or package imagery. It suppresses:

- logos and icons
- nutrition / facts panels
- trust badges
- review graphics
- cross-sell products
- story / tout art
- mug or beans-only coffee context
- accessories and phone cases

For Shopify-style stores, structured JSON-LD and product JSON images get priority.

Manual override is always available via `--reference-image` on `generate-images.py`.

## Live Spend Gates

- Generation is dry by default. Live requires `--live` (`generate-images.py`) or `--live-confirm` (`run-live-proof.sh`).
- Codex native generation is agent-mediated. Use `generate-images.py --provider codex-native` to write `assets/generated/native-generation-requests.json`; Codex must then generate files at the listed paths and update the manifest.
- `run-live-proof.sh` requires both `--live-confirm` and `OPENAI_API_KEY`. Missing either fails fast.
- `--max-shots` defaults small for proofs. Scaling to 12 is a deliberate choice after a 3-shot proof reads cleanly.
- Reroll is dry by default. Use `--reroll live` only with intentional approval.

## Data Files

| File | Purpose |
|------|---------|
| `<packet>/scout.json` | Product facts, page evidence, source images, structured extraction |
| `<packet>/preservation.json` | Must-preserve packaging, label, claim, geometry constraints |
| `<packet>/visual-gaps.json` | Prioritized gap table |
| `<packet>/shoot-plan.json` | Category-aware shot plan |
| `<packet>/prompts.json` | Shot-specific prompts with negatives |
| `<packet>/assets/generated/generation-manifest.json` | Per-shot generation provenance |
| `<packet>/assets/generated/qa-results.json` | Weighted scores plus reroll queue |
| `<packet>/assets/generated/reroll-manifest.json` | Reroll attempts and final status |
| `<packet>/assets/exports/**` | Channel-rendered assets with dimensions metadata |
| `<packet>/assets/review/contact-sheet.html` | Legacy review dashboard |
| `<packet>/index.html` | Magic-moment frontend |

## The Complete Loop

```text
1. ./doctor.sh                              → Verify environment
2. ./evals/run.py                           → Verify deterministic contracts
3. run-live-proof.sh --dry-run              → No-spend end-to-end proof
4. Inspect <packet>/index.html              → Confirm structure and provenance
5. run-live-proof.sh --live-confirm         → 3-shot live proof
6. references/live-qa-calibration.md        → Calibrate QA against human review
7. Scale to 12 shots only after 3 reads cleanly
8. Memory writer captures what worked       → Compounds for the next brand
```

## Safety Rule

If the reference imagery cannot be trusted, surface that.
If category guardrails are missing, label the run honestly and downgrade.
If QA fails and reroll exhausts, leave the shot in the queue. Do not pass it.

Honesty over polish. Every run.
