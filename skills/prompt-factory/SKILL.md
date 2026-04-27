---
name: prompt-factory
description: "Write GPT Image-ready ecommerce product photography prompts from a Brand Shoot Kit shot list and product preservation brief. Use for prompt packs, negative constraints, reroll instructions, and category-aware generation guidance."
metadata:
  openclaw:
    emoji: "🏭"
    user-invocable: true
    primaryEnv: OPENAI_API_KEY
    requires:
      bins: ["python3"]
      env: []
---

# Prompt Factory

Turn a shot list into operational image prompts that preserve the product.

## Each Prompt Must Include

- use case + aspect ratio
- scene and composition
- product placement/scale/handling
- preservation rules
- negative constraints
- specific reroll instruction tied to likely failure

## Avoid

- generic luxury/minimal prompt sludge
- vague “cinematic” adjectives without composition
- fake claims or extra packaging text
- too-small product in commerce shots

Use `scripts/generate-images.py --packet <packet>` for dry-run/live generation manifests.

Executable module owner path:
- `scripts/modules/prompt_factory.py --packet <packet-dir>` -> `prompts.json`
