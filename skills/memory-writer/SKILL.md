---
name: memory-writer
description: "Write reusable Brand Shoot Kit memory after a product shoot: product preservation lessons, winning visual directions, failed prompts, QA risks, and future-shot guidance."
metadata:
  openclaw:
    emoji: "🧠"
    user-invocable: true
    requires:
      bins: ["python3"]
      env: []
---

# Memory Writer

Preserve what will make the next shoot better.

## Capture

- product details that must stay fixed
- angles/compositions that worked
- prompts that failed and why
- label/packaging distortion risks
- channel exports that were most useful
- brand visual language that should repeat

## Output

Update packet memory files:
- `memory/product-shot-memory.md`
- `memory/visual-profile.md`
- `memory/assets.md`

Keep it short, specific, and reusable. No diary prose.

Executable module owner path:
- `scripts/modules/memory_writer.py --packet <packet-dir>` -> updates all `memory/*.md` files
