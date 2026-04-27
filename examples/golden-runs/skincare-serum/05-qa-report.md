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

### Run qa-20260427T175934Z
- Timestamp (UTC): 20260427T175934Z
- Mode: deterministic-manual
- Source manifest: `/home/matt/clawd/projects/brand-shoot-kit/examples/golden-runs/skincare-serum/assets/generated/generation-manifest.json`
- Pass: 0 / 12
- Fail: 0
- Manual review required: 12

| Asset | Status | Score | Top Reasons |
|---|---|---:|---|
| shot-01 (Front label hero) | manual_review | 70.7 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-02 (Dropper angle detail) | manual_review | 74.15 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Ingredient texture smear) | manual_review | 67.05 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-04 (Sink routine placement) | manual_review | 73.4 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Morning hand-held scale) | manual_review | 71.15 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-06 (Shelf trio context) | manual_review | 70.95 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-07 (Body crop application) | manual_review | 68.55 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email routine hero) | manual_review | 66.95 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Seasonal gift bundle) | manual_review | 64.05 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 70.45 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social benefit square) | manual_review | 76.1 | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-12 (Story routine vertical) | manual_review | 66.5 | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |

## Reroll History

### Reroll Run reroll-20260427T175934Z
- Timestamp (UTC): 20260427T175934Z
- Mode: dry-run-simulated
- Eligible shots: 12
- Converged: 11
- Exhausted: 1

| Asset | Original Status | Attempts | Final Status | Reason |
|---|---|---:|---|---|
| shot-01 (Front label hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-02 (Dropper angle detail) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-03 (Ingredient texture smear) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-04 (Sink routine placement) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-05 (Morning hand-held scale) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-06 (Shelf trio context) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-07 (Body crop application) | manual_review | 2 | reroll_exhausted | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-08 (Email routine hero) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-09 (Seasonal gift bundle) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-10 (Marketplace white-ground) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
| shot-11 (Social benefit square) | manual_review | 1 | pass_after_reroll | dry-run placeholder asset requires manual visual review; product framing may be too weak for commerce |
| shot-12 (Story routine vertical) | manual_review | 2 | pass_after_reroll | dry-run placeholder asset requires manual visual review; possible label/geometry mismatch risk |
