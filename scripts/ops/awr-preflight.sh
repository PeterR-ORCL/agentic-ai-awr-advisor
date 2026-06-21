#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"

present_or_missing() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    printf 'present'
  else
    printf 'missing'
  fi
}

tool_status() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf 'OK: %s (%s)\n' "$name" "$(command -v "$name")"
  else
    printf 'MISSING: %s\n' "$name"
  fi
}

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Project directory not found: $PROJECT_DIR" >&2
  exit 1
fi

cd "$PROJECT_DIR"

if [[ -r "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

echo "Project: $PROJECT_DIR"
echo "Branch: $(git branch --show-current 2>/dev/null || true)"
echo

echo "Recent commits:"
git log --oneline -12 2>/dev/null || true
echo

echo "Git status:"
git status --short 2>/dev/null || true
echo

echo "Tracked diff stat:"
git diff --stat 2>/dev/null || true
echo

echo "Tracked diff files:"
git diff --name-only 2>/dev/null || true
echo

echo "Staged files:"
git diff --cached --name-only 2>/dev/null || true
echo

echo "Environment: $ENV_FILE"
printf 'APP_MODE=%s\n' "${APP_MODE:-unset}"
printf 'USE_OCI=%s\n' "${USE_OCI:-unset}"
printf 'USE_LLM=%s\n' "${USE_LLM:-unset}"
printf 'ADB_USER=%s\n' "${ADB_USER:-missing}"
printf 'ADB_DSN=%s\n' "${ADB_DSN:-missing}"
printf 'TNS_ADMIN=%s\n' "${TNS_ADMIN:-missing}"
printf 'OCI_REGION=%s\n' "${OCI_REGION:-missing}"
printf 'ADB_OCID=%s\n' "$(present_or_missing ADB_OCID)"
printf 'OCI_AWR_PREFIX=%s\n' "$(present_or_missing OCI_AWR_PREFIX)"
echo

echo "AI settings:"
printf 'AI_PROVIDER=%s\n' "${AI_PROVIDER:-missing}"
printf 'OCI_MODEL=%s\n' "${OCI_MODEL:-missing}"
printf 'OCI_MODEL_ID=%s\n' "$(present_or_missing OCI_MODEL_ID)"
printf 'OCI_COMPARTMENT_ID=%s\n' "$(present_or_missing OCI_COMPARTMENT_ID)"
printf 'OPENAI_MODEL=%s\n' "${OPENAI_MODEL:-missing}"
printf 'OPENAI_API_KEY=%s\n' "$(present_or_missing OPENAI_API_KEY)"
echo

echo "Tool checks:"
tool_status git
tool_status python
tool_status python3
tool_status pip
tool_status pip3
tool_status node
tool_status npm
tool_status sql
tool_status oci
tool_status rclone
echo

if [[ -n "${TNS_ADMIN:-}" ]]; then
  if [[ -d "$TNS_ADMIN" ]]; then
    echo "Wallet directory exists: $TNS_ADMIN"
  else
    echo "Wallet directory missing: $TNS_ADMIN"
  fi
fi
