#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 --brand NAME --product NAME [--date YYYY-MM-DD] [--root DIR]

Create a standard output folder for a brand/product shoot packet.
USAGE
}

BRAND=""
PRODUCT=""
DATE="$(date +%F)"
ROOT="./output"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --brand) BRAND="$2"; shift 2 ;;
    --product) PRODUCT="$2"; shift 2 ;;
    --date) DATE="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$BRAND" || -z "$PRODUCT" ]]; then
  echo "--brand and --product are required" >&2
  usage
  exit 1
fi

slug() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'
}

OUT_DIR="${ROOT%/}/$(slug "$BRAND")/$(slug "$PRODUCT")/${DATE}"
mkdir -p "$OUT_DIR"/{assets/{pdp,lifestyle,model,seasonal,social,email,marketplace},memory}

for f in 00-brand-analysis.md 01-visual-gap-audit.md 02-shoot-strategy.md 03-shot-list.md 04-generation-prompts.md 05-qa-report.md 06-export-map.md; do
  [[ -f "$OUT_DIR/$f" ]] || : > "$OUT_DIR/$f"
done

[[ -f "$OUT_DIR/memory/visual-profile.md" ]] || : > "$OUT_DIR/memory/visual-profile.md"
[[ -f "$OUT_DIR/memory/product-shot-memory.md" ]] || : > "$OUT_DIR/memory/product-shot-memory.md"
[[ -f "$OUT_DIR/memory/assets.md" ]] || : > "$OUT_DIR/memory/assets.md"

echo "$OUT_DIR"
