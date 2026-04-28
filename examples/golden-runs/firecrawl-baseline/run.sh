#!/usr/bin/env bash
set -euo pipefail

# Golden run: exercises the Firecrawl scraper branch end-to-end via fixture replay.
# Usage: ./run.sh <output-dir>

OUT="${1:?output dir required}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

export BSK_FIRECRAWL_FIXTURE_DIR="$ROOT/evals/fixtures/firecrawl"
export BSK_FORCE_SCRAPER="firecrawl"

mkdir -p "$OUT"
"$ROOT/scripts/modules/brand_scout.py" \
    --url "https://example.com/products/sample" \
    --out "$OUT/scout.json" \
    --scraper firecrawl
