# Firecrawl response fixtures

This directory holds verbatim Firecrawl `/v2/scrape` response bodies used by the
Firecrawl adapter in fixture mode.

Each file is named by `sha256(url)` and contains:

```json
{
  "request": {
    "url": "<the URL>",
    "recorded_at": "<ISO8601>",
    "firecrawl_endpoint": "/v2/scrape"
  },
  "response": { "success": true, "data": { ... } }
}
```

## Recording a new fixture

```bash
export FIRECRAWL_API_KEY=...
./scripts/record-firecrawl-fixture.py --url "https://example.com/products/foo"
```

This is the only path that hits Firecrawl during testing. `./evals/run.py`
never makes live calls.

## Refresh policy

Re-record when:
- The Firecrawl request schema changes.
- The `structured_product` JSON-schema changes.
- A new category needs a Firecrawl-rendered example.

Fixtures are not time-sensitive — they test adapter normalization of a known
response, not live PDP state.
