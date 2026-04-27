---
name: export-packager
description: "Package approved Brand Shoot Kit assets into channel-specific ecommerce export folders and manifests. Use for PDP/social/email/marketplace maps, naming, export manifests, and handoff-ready asset organization."
metadata:
  openclaw:
    emoji: "📦"
    user-invocable: true
    requires:
      bins: ["python3"]
      env: []
---

# Export Packager

Make the shoot usable after generation.

## Output

Create channel-organized exports:
- PDP
- lifestyle
- model
- social
- email
- marketplace

Include manifest fields: source shot, channel, ratio, QA status, file path, recommended placement.

Use `scripts/export-packager.py --packet <packet>` for deterministic packaging.

## Rule

Do not bury the user in a pile of files. Name and map assets so a marketer knows exactly where each one goes.
