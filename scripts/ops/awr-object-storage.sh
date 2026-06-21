#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"
ACTION="${1:-ls}"
shift || true

load_env() {
  if [[ ! -r "$ENV_FILE" ]]; then
    echo "Missing .env: $ENV_FILE" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "$1 is not installed or not in PATH." >&2
    exit 127
  }
}

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Required project setting is missing: $name" >&2
    exit 1
  fi
}

load_env
require_cmd rclone
require_var OCI_AWR_PREFIX

case "$ACTION" in
  ls)
    rclone ls "$OCI_AWR_PREFIX"
    ;;

  push)
    rclone copy "$PROJECT_DIR/data/input" "$OCI_AWR_PREFIX" --include '*.out'
    ;;

  sync)
    rclone sync "$PROJECT_DIR/data/input" "$OCI_AWR_PREFIX" --include '*.out'
    ;;

  sync-dry)
    rclone sync "$PROJECT_DIR/data/input" "$OCI_AWR_PREFIX" --include '*.out' --dry-run
    ;;

  clean)
    printf 'Delete all .out files from %s? Type YES to continue: ' "$OCI_AWR_PREFIX"
    read -r reply
    if [[ "$reply" != "YES" ]]; then
      echo "Cancelled."
      exit 1
    fi
    rclone delete "$OCI_AWR_PREFIX" --include '*.out'
    ;;

  put)
    file="${1:-}"
    if [[ -z "$file" || ! -f "$file" ]]; then
      echo "Usage: scripts/object-storage.sh put FILE" >&2
      exit 1
    fi
    rclone copy "$file" "$OCI_AWR_PREFIX"
    ;;

  del)
    file="${1:-}"
    if [[ -z "$file" ]]; then
      echo "Usage: scripts/object-storage.sh del FILE" >&2
      exit 1
    fi
    rclone deletefile "$OCI_AWR_PREFIX/$(basename "$file")"
    ;;

  *)
    echo "Usage: scripts/object-storage.sh [ls|push|sync|sync-dry|clean|put FILE|del FILE]" >&2
    exit 1
    ;;
esac
