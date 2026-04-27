---
name: brand-scout
description: "Extract brand/product evidence from an ecommerce product URL before any Brand Shoot Kit planning or generation. Use for PDP scouting, source evidence capture, product image URL collection, degraded-mode notes, and scout.json creation. Do not use for ad spying or competitor ad research."
metadata:
  openclaw:
    emoji: "🔎"
    user-invocable: true
    requires:
      bins: ["bash", "python3"]
      env: []
---

# Brand Scout

Capture evidence before strategy. Your job is not to be creative yet; it is to prevent hallucinated creative direction.

## Output Contract

Produce `scout.json` with:
- `url`, `title`, `meta_description`, `og_title`, `og_description`
- `h1[]`, `image_urls[]`
- visible product/category/tone clues
- `degraded_mode` and `note`

Use `scripts/scout-url.sh` for lightweight extraction and `scripts/run-brand-shoot.py --url` when creating a packet.

## Rules

- Evidence first, inference second.
- Mark confidence. Do not launder guesses into facts.
- If fetch fails, ask for PDP copy plus 3-5 product image URLs/uploads.
- Never scrape gated/private pages.
- Never drift into ad intelligence.

## Quality Bar

A downstream agent should be able to cite where each product, tone, visual, and preservation clue came from.
