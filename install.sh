#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="brand-shoot-kit"
TARGET_BASE="${HOME}/.clawd/skills"
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: $0 [--target PATH] [--dry-run] [--help]

Install ${SKILL_NAME} into a reusable local skills directory.

Options:
  --target PATH   Base directory where the skill folder is installed (default: ${TARGET_BASE})
  --dry-run       Show actions without copying files
  --help          Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_BASE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

TARGET_DIR="${TARGET_BASE%/}/${SKILL_NAME}"

echo "Installing to: ${TARGET_DIR}"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] mkdir -p '${TARGET_BASE}'"
  echo "[dry-run] rsync -a --delete '${SCRIPT_DIR}/' '${TARGET_DIR}/'"
  exit 0
fi

mkdir -p "$TARGET_BASE"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git/' \
    --exclude 'output/' \
    --exclude '__pycache__/' \
    "$SCRIPT_DIR/" "$TARGET_DIR/"
else
  rm -rf "$TARGET_DIR"
  mkdir -p "$TARGET_DIR"
  cp -R "$SCRIPT_DIR"/. "$TARGET_DIR"/
  rm -rf "$TARGET_DIR/.git" "$TARGET_DIR/output"
fi

echo "Install complete: ${TARGET_DIR}"
