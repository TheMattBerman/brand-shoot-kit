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

### Run qa-20260427T220658Z
- Timestamp (UTC): 20260427T220658Z
- Mode: deterministic-manual
- Source manifest: `/home/matt/clawd/projects/brand-shoot-kit/examples/golden-runs/supplement-greens/assets/generated/generation-manifest.json`
- Pass: 0 / 12
- Fail: 0
- Manual review required: 12

| Asset | Status | Score | Top Reasons |
|---|---|---:|---|
| shot-01 (Clean front tub hero) | manual_review | 73.6 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Supplement-facts label/detail angle) | manual_review | 70.6 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Powder texture + supporting props) | manual_review | 70.75 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-04 (Morning counter product-in-use routine) | manual_review | 68.75 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Hand-held shake scale proof) | manual_review | 75.3 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents kitchen layout) | manual_review | 79.0 | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Human body-crop mixing in-use) | manual_review | 70.15 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-08 (Email routine hero) | manual_review | 71.85 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Seasonal wellness gifting) | manual_review | 64.25 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 70.4 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-11 (Social trust square) | manual_review | 75.25 | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-12 (Story prep vertical) | manual_review | 73.4 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |

## Reroll History

### Reroll Run reroll-20260427T220658Z
- Timestamp (UTC): 20260427T220658Z
- Mode: dry-run-simulated
- Eligible shots: 12
- Converged: 11
- Exhausted: 1

| Asset | Original Status | Attempts | Final Status | Reason |
|---|---|---:|---|---|
| shot-01 (Clean front tub hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-02 (Supplement-facts label/detail angle) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Powder texture + supporting props) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-04 (Morning counter product-in-use routine) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Hand-held shake scale proof) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-06 (Bundle + contents kitchen layout) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; weighted score below threshold |
| shot-07 (Human body-crop mixing in-use) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-08 (Email routine hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Seasonal wellness gifting) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-11 (Social trust square) | manual_review | 2 | reroll_exhausted | dry-run placeholder asset requires manual visual review; possible soft-focus or legibility issue |
| shot-12 (Story prep vertical) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
