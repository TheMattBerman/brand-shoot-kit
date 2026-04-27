---
name: product-preservation
description: "Create the immutable product truth and preservation brief for Brand Shoot Kit outputs. Use when product shape, packaging, label text, claims, variants, compliance, or distortion risk must be protected before image generation."
metadata:
  openclaw:
    emoji: "🧴"
    user-invocable: true
    requires:
      bins: ["python3"]
      env: []
---

# Product Preservation

Pretty-but-wrong images fail. Protect the product before prompts get creative.

## Required Block

```markdown
## Product Preservation Brief
- Product type:
- Must preserve:
- Can vary:
- Never change:
- Distortion risks:
- Accuracy confidence:
```

## Rules

- Never invent label claims, certifications, badges, flavors, ingredients, or variants.
- Bias toward clean PDP/product-in-context shots when confidence is low.
- Flag transparent/glass/reflective packaging, tiny text, luxury detail, jewelry, and regulated categories as high risk.
- Treat exact packaging text as reference-only unless user explicitly allows concept edits.

## Output

A preservation brief that `prompt-factory` can paste into every generation prompt and `qa-reroll` can score against.

Executable module owner path:
- `scripts/modules/product_preservation.py --packet <packet-dir>` -> `preservation.json`
