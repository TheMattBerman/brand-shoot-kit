#!/usr/bin/env bash
set -euo pipefail

# Thin shim: delegates to scripts/adapters/curl_scrape.py.
# The Python adapter is the source of truth; this script preserves backward compatibility for
# direct callers (e.g. operator muscle memory, brand_scout.py shell-out path).

usage() {
  cat <<USAGE
Usage: $0 --url PRODUCT_URL [--out FILE]

Fetch lightweight product page context (title, description, image URLs) using the curl adapter.
USAGE
}

URL=""
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url) URL="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$URL" ]]; then
  echo "--url is required" >&2
  usage
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

JSON_OUT=$(ROOT_DIR="$ROOT" URL="$URL" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["ROOT_DIR"]) / "scripts"))
from adapters.curl_scrape import scrape

print(json.dumps(scrape(os.environ["URL"]), indent=2))
PY
)

if [[ -n "$OUT" ]]; then
  mkdir -p "$(dirname "$OUT")"
  printf '%s\n' "$JSON_OUT" > "$OUT"
  echo "$OUT"
else
  printf '%s\n' "$JSON_OUT"
fi
