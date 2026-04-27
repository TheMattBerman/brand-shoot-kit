---
name: visual-gap-audit
description: "Audit an ecommerce product page's missing visual assets for Brand Shoot Kit. Use for PDP/lifestyle/model/detail/marketplace/social/email gap matrices and conversion-priority shot recommendations."
metadata:
  openclaw:
    emoji: "🧩"
    user-invocable: true
    requires:
      bins: ["python3"]
      env: []
---

# Visual Gap Audit

Find the missing shots that would make the product easier to understand, trust, and buy.

## Check For

- clean hero / neutral background
- scale/context
- in-use lifestyle
- model/hand interaction
- detail/texture/ingredient/material
- bundle/group shot
- comparison/benefit visual
- email hero
- social crops
- marketplace-compliant image

## Output

`01-visual-gap-audit.md` with each shot type marked:
- `present strong`
- `present weak`
- `missing`
- `not relevant`

Prioritize high-conversion missing shots. Do not recommend a giant shoot just because you can.

Executable module owner path:
- `scripts/modules/visual_gap_audit.py --packet <packet-dir>` -> `visual-gaps.json`
