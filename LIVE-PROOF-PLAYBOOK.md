# Live Proof Playbook

This playbook runs one real product URL with strict spend gates.

Live quality is unproven until a real run is reviewed by a human.

## 1) Choose Product URL

Use a product URL that has:
- clear pack shots and readable label text
- obvious product geometry (bottle/jar/bag shape)
- stable PDP content (not temporary campaign pages)

Avoid pages with paywalls, heavy geo-gating, or missing product imagery.

## 2) Run Dry Proof First (No Spend)

```bash
./scripts/run-live-proof.sh \
  --dry-run \
  --url "https://example.com/products/sample" \
  --out output/live-proof-dry/sample \
  --max-shots 3
```

## 3) Inspect Packet Before Live

Review:
- `scout.json`
- `preservation.json`
- `04-generation-prompts.md`
- `05-qa-report.md`
- `LIVE_PROOF_SUMMARY.md`

Confirm prompts preserve product truth and reject risky drift.

## 4) Run Live 3-Shot Proof (Only After Approval)

Requirements:
- `OPENAI_API_KEY` set
- explicit `--live-confirm`

```bash
./scripts/run-live-proof.sh \
  --live-confirm \
  --url "https://REAL_PRODUCT_URL" \
  --out output/live-proof/real-product/$(date +%F) \
  --max-shots 3 \
  --reroll dry
```

Notes:
- Default `--reroll dry` avoids extra paid calls while still testing reroll logic.
- Use `--reroll live` only when you intentionally approve live reroll spend.

## 5) Run QA Calibration Review

After live run:
- use `references/live-qa-calibration.md`
- copy and fill `examples/live-proof-review-template.json` into the run folder
- record product accuracy, label fidelity, realism, and reroll quality

## 6) Decide Expansion to 12 Shots

Scale from 3 to 12 only when:
- human review confirms product and label fidelity
- QA/reject reasons are coherent
- at least one proof image is directly usable

If not approved, tune thresholds/prompts/reroll instructions and rerun another 3-shot proof first.
