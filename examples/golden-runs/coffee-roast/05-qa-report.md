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

### Run qa-20260427T212057Z
- Timestamp (UTC): 20260427T212057Z
- Mode: deterministic-manual
- Source manifest: `/home/matt/clawd/projects/brand-shoot-kit/examples/golden-runs/coffee-roast/assets/generated/generation-manifest.json`
- Pass: 0 / 12
- Fail: 0
- Manual review required: 12

| Asset | Status | Score | Top Reasons |
|---|---|---:|---|
| shot-01 (Clean front pack hero) | manual_review | 63.5 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Roast label/detail angle) | manual_review | 62.7 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Beans texture + supporting props) | manual_review | 66.5 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-04 (Pour-over product-in-use counter scene) | manual_review | 70.4 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-05 (Hand scoop scale proof) | manual_review | 64.45 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents pantry spread) | manual_review | 76.15 | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Human brew body-crop in-use) | manual_review | 70.05 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email morning hero) | manual_review | 73.1 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-09 (Holiday gifting stack) | manual_review | 75.3 | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-10 (Marketplace white-ground) | manual_review | 78.3 | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-11 (Social brew square) | manual_review | 72.85 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-12 (Story brew vertical) | manual_review | 71.85 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |

## Reroll History

### Reroll Run reroll-20260427T212057Z
- Timestamp (UTC): 20260427T212057Z
- Mode: dry-run-simulated
- Eligible shots: 12
- Converged: 11
- Exhausted: 1

| Asset | Original Status | Attempts | Final Status | Reason |
|---|---|---:|---|---|
| shot-01 (Clean front pack hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Roast label/detail angle) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Beans texture + supporting props) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-04 (Pour-over product-in-use counter scene) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-05 (Hand scoop scale proof) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents pantry spread) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Human brew body-crop in-use) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email morning hero) | manual_review | 2 | reroll_exhausted | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-09 (Holiday gifting stack) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-10 (Marketplace white-ground) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-11 (Social brew square) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-12 (Story brew vertical) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
