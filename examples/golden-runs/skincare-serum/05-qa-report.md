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

### Run qa-20260427T215450Z
- Timestamp (UTC): 20260427T215450Z
- Mode: deterministic-manual
- Source manifest: `/home/matt/clawd/projects/brand-shoot-kit/examples/golden-runs/skincare-serum/assets/generated/generation-manifest.json`
- Pass: 0 / 12
- Fail: 0
- Manual review required: 12

| Asset | Status | Score | Top Reasons |
|---|---|---:|---|
| shot-01 (Clean front label hero) | manual_review | 65.4 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Dropper label/detail angle) | manual_review | 70.4 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Ingredient texture + supporting props) | manual_review | 70.9 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-04 (Sink routine product-in-use scene) | manual_review | 70.85 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Morning hand-held scale proof) | manual_review | 67.75 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents layout) | manual_review | 64.8 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-07 (Human body-crop application in-use) | manual_review | 69.7 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email routine hero) | manual_review | 72.8 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-09 (Seasonal gift bundle) | manual_review | 63.1 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 73.3 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social benefit square) | manual_review | 75.0 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-12 (Story routine vertical) | manual_review | 69.8 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |

## Reroll History

### Reroll Run reroll-20260427T215450Z
- Timestamp (UTC): 20260427T215450Z
- Mode: dry-run-simulated
- Eligible shots: 12
- Converged: 12
- Exhausted: 0

| Asset | Original Status | Attempts | Final Status | Reason |
|---|---|---:|---|---|
| shot-01 (Clean front label hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Dropper label/detail angle) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Ingredient texture + supporting props) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-04 (Sink routine product-in-use scene) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Morning hand-held scale proof) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents layout) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-07 (Human body-crop application in-use) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email routine hero) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-09 (Seasonal gift bundle) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social benefit square) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-12 (Story routine vertical) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
