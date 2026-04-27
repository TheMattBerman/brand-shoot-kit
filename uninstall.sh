#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="brand-shoot-kit"
TARGET_BASE="${HOME}/.clawd/skills"
FORCE=0

usage() {
  cat <<USAGE
Usage: $0 [--target PATH] [--force] [--help]

Uninstall ${SKILL_NAME} from local skills directory.

Options:
  --target PATH   Base directory where skill is installed (default: ${TARGET_BASE})
  --force         Skip confirmation
  --help          Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_BASE="$2"
      shift 2
      ;;
    --force)
      FORCE=1
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
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Not installed at: ${TARGET_DIR}"
  exit 0
fi

if [[ "$FORCE" -ne 1 ]]; then
  read -r -p "Remove '${TARGET_DIR}'? [y/N] " reply
  if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
  fi
fi

rm -rf "$TARGET_DIR"
echo "Removed: ${TARGET_DIR}"
echo "Note: project output in your workspace is preserved."
