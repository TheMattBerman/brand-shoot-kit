# brand-scout contract

Input:
- `product_url` (required)
- optional `brand_urls[]`

Output artifact:
- `scout.json`

Required fields:
- `url`, `title`, `meta_description`, `og_title`, `og_description`
- `h1[]`, `image_urls[]`, `degraded_mode`, `note`
- `product_name`, `brand_name`, `product_type`, `product_category`, `price`
- `variants[]`, `claims_benefits[]`, `ingredients_materials_specs[]`
- `visible_packaging_text_candidates[]`, `image_evidence[]`
- `field_confidence{}`, `extraction_warnings[]`

Executable owner:
- `scripts/modules/brand_scout.py`

Failure mode:
- if fetch fails, request user-pasted PDP copy and 3-5 image URLs.
