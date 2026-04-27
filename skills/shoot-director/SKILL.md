---
name: shoot-director
description: "Turn Brand Shoot Kit evidence and gaps into a focused ecommerce shoot strategy and 12-shot production plan. Use for creative direction, set/model choices, channel ratios, and production sequencing."
metadata:
  openclaw:
    emoji: "🎬"
    user-invocable: true
    requires:
      bins: ["python3"]
      env: []
---

# Shoot Director

Make taste decisions. Do not dump options.

## Flow

1. Offer 2-3 viable directions.
2. Pick one default direction with rationale.
3. Build a practical 12-shot plan across PDP, lifestyle, model, detail, social, email, marketplace.
4. Assign channel, ratio, priority, and preservation risk per shot.

## Defaults

- 12 shots unless user asks otherwise.
- Hands/body crops beat uncanny full-face model scenes when the product does not need a face.
- Brand fit and product clarity beat cinematic vibes.

## Output

`02-shoot-strategy.md` and `03-shot-list.md` ready for prompt generation.

Executable module owner path:
- `scripts/modules/shoot_director.py --packet <packet-dir>` -> `shoot-plan.json`
