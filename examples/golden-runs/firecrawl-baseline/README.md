# firecrawl-baseline golden run

Exercises the Firecrawl scraper branch of `scripts/modules/brand_scout.py` end-to-end
without touching the live Firecrawl API.

## How it works

`run.sh` sets two env vars:

- `BSK_FORCE_SCRAPER=firecrawl` — overrides the eval harness default of `curl`.
- `BSK_FIRECRAWL_FIXTURE_DIR=<repo>/evals/fixtures/firecrawl` — replays the recorded
  response in `1e3e0685…afd592b.json` instead of hitting `api.firecrawl.dev`.

It then invokes `brand_scout.py --scraper firecrawl --url https://example.com/products/sample`
and writes `scout.json` to the directory you pass.

## What this catches

- Adapter normalization regressions (Firecrawl response → scout shape).
- `enrich_scout()` regressions on the Firecrawl-populated branch.
- Schema-extraction drift (the fixture's `structured_product` keys must match the
  schema the live adapter requests).

## What this does NOT catch

- Whether Firecrawl actually returns useful data for any given URL (calibration concern).
- Network-level failures (covered by separate adapter tests).

To re-record the fixture: `./scripts/record-firecrawl-fixture.py --url <URL>` (requires `FIRECRAWL_API_KEY`).
