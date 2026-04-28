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
- `scrape_provenance{}` — object with `scraper` (`"curl"` or `"firecrawl"`), `scraper_version`, `scraped_at`, `request_url`, `fixture_used` (or null), `forced_by` (or null), and `firecrawl_meta` (when `scraper == "firecrawl"`).

Optional fields (populated by Firecrawl adapter only; absent on curl path):
- `rendered_html`, `structured_product{}`, `main_image_url`, `excluded_image_urls[]`, `firecrawl_meta{}`

Executable owner:
- `scripts/modules/brand_scout.py`
- Scraper selection: `--scraper {auto,curl,firecrawl}` flag → `BSK_FORCE_SCRAPER` env → `FIRECRAWL_API_KEY` env → curl default.

Failure mode:
- if curl fetch fails, request user-pasted PDP copy and 3-5 image URLs.
- if Firecrawl fails, dispatcher exits code 2 with a `--scraper curl` recovery hint; operator re-runs with the curl fallback.
