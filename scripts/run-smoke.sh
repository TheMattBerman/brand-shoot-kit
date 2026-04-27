#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SMOKE_OUT="${ROOT_DIR}/output/smoke-test"

rm -rf "$SMOKE_OUT"

"${ROOT_DIR}/scripts/run-brand-shoot.py" \
  --scout-json "${ROOT_DIR}/examples/scout-samples/skincare-serum-scout.json" \
  --brand "Example Skin" \
  --product "Hydrating Face Serum" \
  --out "$SMOKE_OUT"

"${ROOT_DIR}/scripts/validate-packet.py" --packet "$SMOKE_OUT"

"${ROOT_DIR}/scripts/generate-images.py" \
  --packet "$SMOKE_OUT"

"${ROOT_DIR}/scripts/qa-images.py" \
  --packet "$SMOKE_OUT"

"${ROOT_DIR}/scripts/export-packager.py" \
  --packet "$SMOKE_OUT"

GEN_MANIFEST="${SMOKE_OUT}/assets/generated/generation-manifest.json"
QA_RESULTS="${SMOKE_OUT}/assets/generated/qa-results.json"

[[ -f "$GEN_MANIFEST" ]] || { echo "Missing generation manifest: $GEN_MANIFEST"; exit 1; }
[[ -f "$QA_RESULTS" ]] || { echo "Missing QA results: $QA_RESULTS"; exit 1; }

EXPORT_MANIFEST="$(find "${SMOKE_OUT}/assets/exports" -name 'export-manifest.json' | head -n 1)"
[[ -n "$EXPORT_MANIFEST" && -f "$EXPORT_MANIFEST" ]] || { echo "Missing export manifest"; exit 1; }

echo "Smoke test passed: $SMOKE_OUT"
