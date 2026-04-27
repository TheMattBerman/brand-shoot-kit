# QA Report

## Run Status
- Generation: Not Run (planning mode by default)
- Automated QA: Not Run

## Rubric
| Criterion | Weight | Score | Notes |
|---|---:|---:|---|
| Product accuracy | 30 | TBD | |
| Commerce usefulness | 20 | TBD | |
| Brand fit | 15 | TBD | |
| Scene realism | 15 | TBD | |
| Visual clarity | 10 | TBD | |
| AI artifact risk | 10 | TBD | |

## Automatic Rejection Triggers
- label text changed
- product geometry changed
- unreadable key text
- malformed hand interacting with product
- fake claims/certification
- product too small for commerce utility

## Automated QA Runs

### Run qa-20260427T180755Z
- Timestamp (UTC): 20260427T180755Z
- Mode: deterministic-manual
- Source manifest: `/home/matt/clawd/projects/brand-shoot-kit/examples/golden-runs/coffee-roast/assets/generated/generation-manifest.json`
- Pass: 0 / 12
- Fail: 0
- Manual review required: 12

| Asset | Status | Score | Top Reasons |
|---|---|---:|---|
| shot-01 (Front pack hero) | manual_review | 73.6 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Roast label angle) | manual_review | 65.85 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Beans + bag texture) | manual_review | 81.75 | dry-run placeholder asset requires manual visual review |
| shot-04 (Pour-over counter scene) | manual_review | 82.35 | dry-run placeholder asset requires manual visual review |
| shot-05 (Hand scoop scale) | manual_review | 68.3 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Pantry shelf context) | manual_review | 74.7 | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Steam mug body crop) | manual_review | 74.85 | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-08 (Email morning hero) | manual_review | 64.15 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Holiday gifting stack) | manual_review | 65.15 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 62.7 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social brew square) | manual_review | 76.85 | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-12 (Story brew vertical) | manual_review | 63.95 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |

## Reroll History

### Reroll Run reroll-20260427T180755Z
- Timestamp (UTC): 20260427T180755Z
- Mode: dry-run-simulated
- Eligible shots: 12
- Converged: 12
- Exhausted: 0

| Asset | Original Status | Attempts | Final Status | Reason |
|---|---|---:|---|---|
| shot-01 (Front pack hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Roast label angle) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Beans + bag texture) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review |
| shot-04 (Pour-over counter scene) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review |
| shot-05 (Hand scoop scale) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Pantry shelf context) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Steam mug body crop) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-08 (Email morning hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Holiday gifting stack) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social brew square) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-12 (Story brew vertical) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
