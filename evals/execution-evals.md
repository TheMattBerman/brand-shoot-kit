# Execution Evals

## Eval 1: Skincare Serum

Input: product URL for premium serum.
Expected: preservation brief, texture shot, bathroom lifestyle, no medical claim drift.

## Eval 2: Daily Greens Supplement

Input: supplement bottle PDP.
Expected: kitchen routine context, scoop/use shot, marketplace-safe hero, claim-preservation warning.

## Eval 3: Coffee Bag Launch

Input: coffee product URL.
Expected: bag hero, bean detail, brew context, seasonal optional, no invented origin badges.

## Eval 4: Weak-Fit Product

Input: precision industrial valve.
Expected: fidelity warning, planning-first output, recommendation for real photography for exact specs.

## Eval 5: URL-to-Packet Deterministic Run

Input: `scripts/run-brand-shoot.py --url <product-url>` or `--scout-json <fixture>`.
Expected: generated packet path contains all required docs, memory files, and assets directories; `validate-packet.py` passes.

## Eval 6: Dry-Run Generation -> QA -> Export

Input: `scripts/run-smoke.sh` (or sequentially run `generate-images.py`, `qa-images.py`, `export-packager.py` on a packet).
Expected:
- `assets/generated/generation-manifest.json` exists with shot entries and placeholder image files.
- `assets/generated/qa-results.json` exists with deterministic/manual status and per-criterion scores.
- `05-qa-report.md` is appended with a run section.
- `assets/exports/<run-id>/export-manifest.json` exists with deterministic channel copy records.
