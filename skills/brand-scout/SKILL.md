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
- structured extraction fields:
  `product_name`, `brand_name`, `product_type`, `product_category`, `price`,
  `variants`, `claims_benefits`, `ingredients_materials_specs`,
  `visible_packaging_text_candidates`, `image_evidence`, `field_confidence`,
  `extraction_warnings`
- `degraded_mode` and `note`
- `scrape_provenance` (object) recording which adapter ran:
  `{scraper, scraper_version, scraped_at, request_url, fixture_used, forced_by, firecrawl_meta?}`.

Executable module owner path:
- `scripts/modules/brand_scout.py --url <product-url> --packet <packet-dir>` -> `scout.json`
- `scripts/scout-structured.py --in <scout.json> --out <scout.json>` for structured enrichment only.

Scraper selection on the module:
- `--scraper {auto,curl,firecrawl}` (default `auto`).
- `auto` follows env precedence: `BSK_FORCE_SCRAPER` (used by `./evals/run.py`) → `FIRECRAWL_API_KEY` → curl default.
- Firecrawl failures exit code 2 with a one-line `--scraper curl` recovery hint.

## Rules

- Evidence first, inference second.
- Mark confidence. Do not launder guesses into facts.
- If fetch fails, ask for PDP copy plus 3-5 product image URLs/uploads.
- Never scrape gated/private pages.
- Never drift into ad intelligence.

## Quality Bar

A downstream agent should be able to cite where each product, tone, visual, and preservation clue came from.
