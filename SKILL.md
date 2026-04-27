---
name: brand-shoot-kit
description: "Turn a product URL or product image into a brand-aware ecommerce shoot plan: brand read, visual gap audit, shoot strategy, shot list, GPT Image-ready prompts, QA rubric, and export map. Use for PDP/lifestyle/model/seasonal product photography systems. Do not use for ad spying, competitor ad intelligence, paid-social creative mining, or media-buying analysis."
metadata:
  openclaw:
    emoji: "📸"
    user-invocable: true
    primaryEnv: OPENAI_API_KEY
    requires:
      bins: ["bash", "python3"]
      env: []
---

# Brand Shoot Kit

Run this when the user wants a complete ecommerce product photography system, not one-off prompts.

For module boundaries and stage contracts, use `SUITE.md` plus `references/module-contracts/`.

## Outcome Contract

Produce a runnable shoot packet that includes:
- `00-brand-analysis.md`
- `01-visual-gap-audit.md`
- `02-shoot-strategy.md`
- `03-shot-list.md`
- `04-generation-prompts.md`
- `05-qa-report.md`
- `06-export-map.md`

Also include asset folder targets:
- `assets/pdp`
- `assets/lifestyle`
- `assets/model`
- `assets/seasonal`
- `assets/social`
- `assets/email`
- `assets/marketplace`

## Non-Negotiables

- Product truth beats aesthetics.
- Diagnose before generating.
- Keep the default pack to 12 shots unless asked otherwise.
- Keep ecommerce-first framing; this is not an ad-intelligence workflow.
- If browsing/API/image generation is unavailable, still deliver the full planning packet and GPT Image-ready prompts.

## Flow (Always This Order)

1. Intake: confirm product URL/image, target channels, constraints.
2. Brand analysis: brand tone, audience, price tier, visual language.
3. Product preservation brief: what must never change.
4. Visual gap audit: what is missing and priority.
5. Shoot strategy: 2-3 directions, pick one with rationale.
6. Shot list: practical 12-shot pack with channels + ratios.
7. Prompt pack: one prompt per shot with negative constraints + reroll instruction.
8. QA rubric/report: pass/fail gates and rejection triggers.
9. Export map: where each approved asset goes.
10. Memory: note what to preserve/avoid next run.

When deterministic orchestration is requested (URL/scout JSON -> packet), use:
- `scripts/run-brand-shoot.py` for URL/scout-to-packet
- `scripts/validate-packet.py` for structure validation

## Product Preservation Brief (Required)

Always output this block before prompts:

```markdown
## Product Preservation Brief
- Product type:
- Must preserve:
- Can vary:
- Never change:
- Distortion risks:
- Accuracy confidence:
```

If confidence is low, explicitly say so and bias toward clean commerce shots over aggressive lifestyle edits.

## Anti-Patterns (Block These)

- Starting with moodboard words before diagnosing brand/product.
- 30-50 shot bloated plans by default.
- Fake claims/certifications on labels or props.
- Uncanny face-heavy model scenes when hands/body crop solves the job.
- Generic "luxury minimal" output for every brand.
- Passing pretty but inaccurate images.
- Drifting into ad spy language or competitor ad analysis.

## Prompt Quality Rules

Each shot prompt must include:
- use case + ratio
- scene and composition
- product placement and handling
- preservation rules
- negative constraints
- reroll instruction tied to likely failure

Use plain, operational language. Avoid cinematic fluff.

## Reroll Logic

If any rejection trigger appears, rewrite prompt and reroll that shot:
- changed product shape/label text/logo
- wrong product count or variant
- malformed hands touching product
- fake badges/claims/certifications
- product too small/obscured for commerce use

## Graceful Degradation

When tools/keys are missing:
- still produce full packet
- include "manual generation runbook" section in `04-generation-prompts.md`
- mark image generation as `Not Run` in `05-qa-report.md`

When URL extraction fails:
- ask for pasted PDP copy + 3-5 product image URLs or uploads
- continue workflow with confidence notes

## Calibration Example (Taste)

Weak prompt:
"Create a beautiful premium serum image in a modern bathroom with soft light."

Strong prompt:
"Square 1:1 PDP-support lifestyle image for a 30ml frosted glass serum bottle with matte white dropper cap and front label text preserved exactly from reference. Place bottle upright front-facing on off-white stone vanity, morning side-light from left, shallow depth of field, folded neutral towel and small green leaf in far background blur only. Product occupies ~38% of frame, label fully legible, no extra text or badges, no second bottle, no warped dropper geometry. If label legibility fails, reroll with camera 15% closer and flatter angle."

## Output Style

Write like a creative director + ecommerce merchandiser:
- specific decisions
- explicit tradeoffs
- clear priorities
- no filler sections

For deeper rubrics and templates, use files in `references/` and `examples/`.
