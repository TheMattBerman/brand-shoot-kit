#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0
WARN=0

pass() { echo "PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL+1)); }
warn() { echo "WARN: $1"; WARN=$((WARN+1)); }

check_file() {
  local path="$1"
  [[ -f "$path" ]] && pass "file exists: $path" || fail "missing file: $path"
}

check_dir() {
  local path="$1"
  [[ -d "$path" ]] && pass "dir exists: $path" || fail "missing dir: $path"
}

check_exec() {
  local path="$1"
  if [[ -x "$path" ]]; then
    pass "executable: $path"
  else
    fail "not executable: $path"
  fi
}

check_help() {
  local cmd="$1"
  if eval "$cmd" >/dev/null 2>&1; then
    pass "runs: $cmd"
  else
    fail "failed: $cmd"
  fi
}

echo "Running Brand Shoot Kit doctor..."

# Core structure
check_file "README.md"
check_file "SKILL.md"
check_file "SUITE.md"
check_file "VERSION"
check_file ".env.example"
check_file "openclaw.example.json"
check_file "install.sh"
check_file "doctor.sh"
check_file "uninstall.sh"
check_dir "references"
check_dir "scripts"
check_dir "evals"
check_dir "examples"
check_dir "skills"
check_dir "output"

# Required references
for f in \
  "references/visual-gap-rubric.md" \
  "references/product-preservation.md" \
  "references/ecommerce-shot-taxonomy.md" \
  "references/set-design-patterns.md" \
  "references/model-casting-guide.md" \
  "references/qa-rubric.md" \
  "references/prompt-patterns.md" \
  "references/anti-patterns.md" \
  "references/module-contracts/brand-scout.md" \
  "references/module-contracts/product-preservation.md" \
  "references/module-contracts/visual-gap-audit.md" \
  "references/module-contracts/shoot-director.md" \
  "references/module-contracts/prompt-factory.md" \
  "references/module-contracts/qa-reroll.md" \
  "references/module-contracts/export-packager.md" \
  "references/module-contracts/memory-writer.md"; do
  check_file "$f"
done


# Real suite skills
for f in \
  "skills/brand-scout/SKILL.md" \
  "skills/product-preservation/SKILL.md" \
  "skills/visual-gap-audit/SKILL.md" \
  "skills/shoot-director/SKILL.md" \
  "skills/prompt-factory/SKILL.md" \
  "skills/qa-reroll/SKILL.md" \
  "skills/export-packager/SKILL.md" \
  "skills/memory-writer/SKILL.md"; do
  check_file "$f"
done

# Required evals
check_file "evals/trigger-evals.md"
check_file "evals/execution-evals.md"
check_file "evals/output-quality-rubric.md"
check_file "evals/run.py"
check_file "examples/scout-samples/skincare-serum-scout.json"
check_dir "examples/golden-runs"

# Script checks
for s in \
  "install.sh" \
  "doctor.sh" \
  "uninstall.sh" \
  "scripts/scout-url.sh" \
  "scripts/run-brand-shoot.py" \
  "scripts/run-smoke.sh" \
  "scripts/scaffold-output.sh" \
  "scripts/create-shoot-packet.py" \
  "scripts/validate-packet.py" \
  "scripts/generate-images.py" \
  "scripts/qa-images.py" \
  "scripts/reroll-failed.py" \
  "scripts/export-packager.py" \
  "scripts/scout-structured.py" \
  "scripts/build-golden-runs.sh" \
  "scripts/modules/brand_scout.py" \
  "scripts/modules/product_preservation.py" \
  "scripts/modules/visual_gap_audit.py" \
  "scripts/modules/shoot_director.py" \
  "scripts/modules/prompt_factory.py" \
  "scripts/modules/qa_reroll.py" \
  "scripts/modules/export_packager.py" \
  "scripts/modules/memory_writer.py"; do
  check_exec "$s"
done
check_exec "evals/run.py"

check_help "./install.sh --help"
check_help "./uninstall.sh --help"
check_help "./scripts/scout-url.sh --help"
check_help "./scripts/run-brand-shoot.py --help"
check_help "./scripts/scaffold-output.sh --help"
check_help "./scripts/create-shoot-packet.py --help"
check_help "./scripts/validate-packet.py --help"
check_help "./scripts/generate-images.py --help"
check_help "./scripts/qa-images.py --help"
check_help "./scripts/reroll-failed.py --help"
check_help "./scripts/export-packager.py --help"
check_help "./scripts/scout-structured.py --help"
check_help "./scripts/build-golden-runs.sh --help"
check_help "./scripts/modules/brand_scout.py --help"
check_help "./scripts/modules/product_preservation.py --help"
check_help "./scripts/modules/visual_gap_audit.py --help"
check_help "./scripts/modules/shoot_director.py --help"
check_help "./scripts/modules/prompt_factory.py --help"
check_help "./scripts/modules/qa_reroll.py --help"
check_help "./scripts/modules/export_packager.py --help"
check_help "./scripts/modules/memory_writer.py --help"
check_help "./scripts/run-smoke.sh"
check_help "./evals/run.py"
check_help "./scripts/build-golden-runs.sh"
check_help "./scripts/build-golden-runs.sh --check"

# Basic dependency checks
command -v bash >/dev/null 2>&1 && pass "binary available: bash" || fail "missing binary: bash"
command -v python3 >/dev/null 2>&1 && pass "binary available: python3" || fail "missing binary: python3"

# Optional dependencies
for b in curl jq; do
  if command -v "$b" >/dev/null 2>&1; then
    pass "optional binary available: $b"
  else
    warn "optional binary missing: $b"
  fi
done

# Env capability warnings
for v in OPENAI_API_KEY GOOGLE_AI_API_KEY FIRECRAWL_API_KEY APIFY_API_TOKEN REPLICATE_API_TOKEN; do
  if [[ -n "${!v:-}" ]]; then
    pass "env set: $v"
  else
    warn "env not set (optional): $v"
  fi
done

echo
echo "Summary: PASS=${PASS} FAIL=${FAIL} WARN=${WARN}"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
