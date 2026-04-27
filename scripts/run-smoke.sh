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

echo "Smoke test passed: $SMOKE_OUT"
