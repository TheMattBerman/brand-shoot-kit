# brand-scout contract

Input:
- `product_url` (required)
- optional `brand_urls[]`

Output artifact:
- `scout.json`

Required fields:
- `url`, `title`, `meta_description`, `og_title`, `og_description`
- `h1[]`, `image_urls[]`, `degraded_mode`, `note`

Failure mode:
- if fetch fails, request user-pasted PDP copy and 3-5 image URLs.
