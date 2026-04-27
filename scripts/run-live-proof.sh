#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: ./scripts/run-live-proof.sh --url PRODUCT_URL --out OUTDIR [options]

Operator-safe one-product proof pipeline:
  scout/packet -> generate -> qa -> reroll (optional) -> export -> summary
  live generation auto-selects a safe reference image from scout evidence when available.

Required:
  --url PRODUCT_URL      Product URL to proof
  --out OUTDIR           Output packet directory

Safety controls:
  --dry-run              Force no-spend mode (default when --live-confirm is not set)
  --live-confirm         Explicitly permit live generation/vision calls (requires OPENAI_API_KEY)

Cost controls:
  --max-shots N          Max shots to generate for proof (default: 3)
  --reroll MODE          Reroll mode: off | dry | live (default: dry)

Other:
  --qa-threshold N       QA pass threshold 0-100 (default: 80)
  --help                 Show this help
USAGE
}

URL=""
OUT=""
MAX_SHOTS=3
QA_THRESHOLD=80
REROLL_MODE="dry"
DRY_RUN=false
LIVE_CONFIRM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="${2:-}"
      shift 2
      ;;
    --out)
      OUT="${2:-}"
      shift 2
      ;;
    --max-shots)
      MAX_SHOTS="${2:-}"
      shift 2
      ;;
    --qa-threshold)
      QA_THRESHOLD="${2:-}"
      shift 2
      ;;
    --reroll)
      REROLL_MODE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --live-confirm)
      LIVE_CONFIRM=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$URL" || -z "$OUT" ]]; then
  echo "error: --url and --out are required" >&2
  usage
  exit 1
fi

if [[ "$DRY_RUN" == true && "$LIVE_CONFIRM" == true ]]; then
  echo "error: --dry-run and --live-confirm are mutually exclusive" >&2
  exit 1
fi

case "$REROLL_MODE" in
  off|dry|live) ;;
  *)
    echo "error: --reroll must be one of: off, dry, live" >&2
    exit 1
    ;;
esac

if ! [[ "$MAX_SHOTS" =~ ^[0-9]+$ ]] || [[ "$MAX_SHOTS" -lt 1 ]]; then
  echo "error: --max-shots must be a positive integer" >&2
  exit 1
fi

MODE="dry-run"
if [[ "$LIVE_CONFIRM" == true ]]; then
  MODE="live"
fi
if [[ "$DRY_RUN" == true ]]; then
  MODE="dry-run"
fi

if [[ "$MODE" == "live" ]]; then
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "error: live mode requires OPENAI_API_KEY" >&2
    exit 1
  fi
fi

if [[ "$REROLL_MODE" == "live" && "$MODE" != "live" ]]; then
  echo "error: --reroll live requires --live-confirm" >&2
  exit 1
fi

OUT="$(mkdir -p "$OUT" && cd "$OUT" && pwd)"
RUN_LOG="$OUT/live-proof-commands.log"
SUMMARY="$OUT/LIVE_PROOF_SUMMARY.md"

COMMANDS=()

record_cmd() {
  local rendered=""
  local arg
  for arg in "$@"; do
    printf -v rendered '%s%q ' "$rendered" "$arg"
  done
  COMMANDS+=("${rendered% }")
}

run_cmd() {
  record_cmd "$@"
  "$@"
}

offline_scout_fixture() {
  local url="$1"
  local out_json="$2"
  python3 - "$url" "$out_json" <<'PY'
import json
import sys
from urllib.parse import urlparse

url = sys.argv[1]
out_json = sys.argv[2]

parsed = urlparse(url)
host = parsed.netloc or "example.com"
slug = parsed.path.strip("/") or "product"
name = slug.split("/")[-1].replace("-", " ").replace("_", " ").strip() or "Product"
name = " ".join(x.capitalize() for x in name.split())

payload = {
    "url": url,
    "title": f"{name} | {host}",
    "meta_description": "Offline dry-run scout fallback generated without network.",
    "og_title": f"{name}",
    "og_description": "Dry-run fallback content; replace with real scout evidence before broad rollout.",
    "h1": [name],
    "image_urls": [],
    "degraded_mode": True,
    "note": "offline_fallback_scout_generated_by_run-live-proof.sh",
}

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")
PY
}

echo "[live-proof] mode=${MODE} url=${URL} out=${OUT} max_shots=${MAX_SHOTS} reroll=${REROLL_MODE}"

TMP_SCOUT=""
cleanup() {
  if [[ -n "$TMP_SCOUT" && -f "$TMP_SCOUT" ]]; then
    rm -f "$TMP_SCOUT"
  fi
}
trap cleanup EXIT

# 1) scout + packet
if [[ "$MODE" == "dry-run" ]]; then
  TMP_SCOUT="$(mktemp)"
  set +e
  run_cmd "$ROOT_DIR/scripts/scout-url.sh" --url "$URL" --out "$TMP_SCOUT"
  RC=$?
  set -e
  if [[ "$RC" -ne 0 ]]; then
    echo "[live-proof] scout-url fetch failed; using offline scout fallback for dry-run."
    offline_scout_fixture "$URL" "$TMP_SCOUT"
  fi
  run_cmd "$ROOT_DIR/scripts/run-brand-shoot.py" --scout-json "$TMP_SCOUT" --url "$URL" --out "$OUT"
else
  run_cmd "$ROOT_DIR/scripts/run-brand-shoot.py" --url "$URL" --out "$OUT"
fi

# 2) generate
GEN_CMD=("$ROOT_DIR/scripts/generate-images.py" --packet "$OUT" --limit "$MAX_SHOTS")
if [[ "$MODE" == "live" ]]; then
  GEN_CMD+=(--live --auto-reference-image)
fi
run_cmd "${GEN_CMD[@]}"

# 3) qa
QA_CMD=("$ROOT_DIR/scripts/qa-images.py" --packet "$OUT" --threshold "$QA_THRESHOLD")
if [[ "$MODE" == "live" ]]; then
  QA_CMD+=(--live)
fi
run_cmd "${QA_CMD[@]}"

# 4) reroll (optional)
if [[ "$REROLL_MODE" == "off" ]]; then
  echo "[live-proof] reroll stage skipped (--reroll off)"
else
  REROLL_CMD=("$ROOT_DIR/scripts/reroll-failed.py" --packet "$OUT")
  if [[ "$REROLL_MODE" == "live" ]]; then
    REROLL_CMD+=(--live)
  fi
  run_cmd "${REROLL_CMD[@]}"
fi

# 5) export
run_cmd "$ROOT_DIR/scripts/export-packager.py" --packet "$OUT"

# 6) summary
printf '%s\n' "${COMMANDS[@]}" > "$RUN_LOG"

python3 - "$OUT" "$SUMMARY" "$URL" "$MODE" "$MAX_SHOTS" "$QA_THRESHOLD" "$REROLL_MODE" "$RUN_LOG" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

out = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
url = sys.argv[3]
mode = sys.argv[4]
max_shots = int(sys.argv[5])
qa_threshold = float(sys.argv[6])
reroll_mode = sys.argv[7]
run_log = Path(sys.argv[8])

def load(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

man_gen = out / "assets" / "generated" / "generation-manifest.json"
man_qa = out / "assets" / "generated" / "qa-results.json"
man_reroll = out / "assets" / "generated" / "reroll-manifest.json"

export_manifests = sorted(out.glob("assets/exports/**/export-manifest.json"))
export_manifest = export_manifests[-1] if export_manifests else None

gen = load(man_gen) or {}
qa = load(man_qa) or {}
reroll = load(man_reroll) or {}
export = load(export_manifest) if export_manifest else {}

qa_summary = qa.get("summary", {})
reroll_summary = reroll.get("summary", {})
export_summary = export.get("summary", {})

command_lines = run_log.read_text(encoding="utf-8").strip().splitlines() if run_log.exists() else []

def artifact_line(path):
    return f"- {'present' if path and Path(path).exists() else 'missing'}: `{path}`"

cost_block = [
    "- actual_cost_usd: unknown (not tracked by scripts yet)",
    f"- estimated_max_image_calls: <= {max_shots} + live reroll attempts (if enabled)",
    f"- estimated_max_vision_calls: <= {max_shots} when live QA is enabled",
]
if mode != "live":
    cost_block.append("- paid_calls_executed: 0 (dry-run mode)")

next_decisions = [
    "- Confirm product accuracy and label fidelity manually against source page/screenshots.",
    "- Review reroll reasons and decide threshold/rubric tuning before scaling.",
    "- Expand to 12 shots only after this proof is judged production-usable by human review.",
]

lines = [
    "# LIVE_PROOF_SUMMARY",
    "",
    "## Run Inputs",
    f"- timestamp_utc: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    f"- mode: {mode}",
    f"- product_url: {url}",
    f"- out_dir: {out}",
    f"- max_shots: {max_shots}",
    f"- qa_threshold: {qa_threshold}",
    f"- reroll_mode: {reroll_mode}",
    "",
    "## Commands Run",
]

if command_lines:
    lines.extend([f"- `{c}`" for c in command_lines])
else:
    lines.append("- none recorded")

lines.extend(
    [
        "",
        "## Artifacts",
        artifact_line(man_gen),
        artifact_line(man_qa),
        artifact_line(man_reroll),
        artifact_line(export_manifest) if export_manifest else "- missing: export manifest",
        "",
        "## Outcome Snapshot",
        f"- generated_entries: {len(gen.get('entries', []) or [])}",
        f"- qa_total: {qa_summary.get('total', 0)}",
        f"- qa_pass: {qa_summary.get('pass', 0)}",
        f"- qa_fail: {qa_summary.get('fail', 0)}",
        f"- qa_manual_review: {qa_summary.get('manual_review', 0)}",
        f"- reroll_eligible_shots: {reroll_summary.get('eligible_shots', 0)}",
        f"- reroll_pass_after_reroll: {reroll_summary.get('pass_after_reroll', 0)}",
        f"- reroll_exhausted: {reroll_summary.get('reroll_exhausted', 0)}",
        f"- export_packaged_assets: {export_summary.get('packaged_assets', 0)}",
        f"- export_copied_files: {export_summary.get('copied_files', 0)}",
        "",
        "## Cost Tracking",
    ]
)
lines.extend(cost_block)

lines.extend(
    [
        "",
        "## Next Decisions",
    ]
)
lines.extend(next_decisions)
lines.append("")

summary_path.write_text("\n".join(lines), encoding="utf-8")
print(summary_path)
PY

echo "[live-proof] summary: $SUMMARY"
