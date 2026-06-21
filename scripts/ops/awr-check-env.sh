#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"
ISSUES=0

require_present() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    printf 'OK: %s\n' "$name"
  else
    printf 'MISSING: %s\n' "$name"
    ISSUES=$((ISSUES + 1))
  fi
}

show_present() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    printf 'present: %s\n' "$name"
  else
    printf 'missing: %s\n' "$name"
  fi
}

if [[ ! -r "$ENV_FILE" ]]; then
  echo "Agentic AI AWR Advisor environment check"
  echo "Project: $PROJECT_DIR"
  echo "MISSING: .env file is not readable: $ENV_FILE"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

MODE="${APP_MODE:-oracle}"
USE_LLM_VALUE="${USE_LLM:-false}"
AI_PROVIDER_VALUE="${AI_PROVIDER:-}"

echo "Agentic AI AWR Advisor environment check"
echo "Project: $PROJECT_DIR"
echo "Mode: $MODE"
echo

echo "Required database settings:"
if [[ "$MODE" != "mock" ]]; then
  require_present ADB_USER
  require_present ADB_DSN
  require_present TNS_ADMIN
else
  echo "mock mode: database settings not required"
fi

echo

echo "OCI settings:"
if [[ "$MODE" != "mock" ]]; then
  require_present OCI_REGION
  require_present ADB_OCID
  show_present OCI_CONFIG_FILE
  show_present OCI_CONFIG_PROFILE
else
  echo "mock mode: OCI settings not required"
fi

echo

echo "Object Storage:"
show_present OCI_AWR_PREFIX

echo

echo "AI settings:"
printf 'AI_PROVIDER: %s\n' "${AI_PROVIDER_VALUE:-unset}"
printf 'USE_LLM:     %s\n' "${USE_LLM_VALUE:-unset}"

if [[ "$USE_LLM_VALUE" == "true" || "$USE_LLM_VALUE" == "1" || "$MODE" == "full" ]]; then
  require_present AI_PROVIDER

  case "${AI_PROVIDER_VALUE}" in
    oci)
      require_present OCI_MODEL
      require_present OCI_MODEL_ID
      require_present OCI_COMPARTMENT_ID
      require_present OCI_CONFIG_FILE
      require_present OCI_CONFIG_PROFILE
      require_present OCI_REGION
      show_present OPENAI_MODEL
      show_present OPENAI_API_KEY
      ;;
    openai)
      require_present OPENAI_MODEL
      require_present OPENAI_API_KEY
      ;;
    "")
      :
      ;;
    *)
      printf 'UNKNOWN AI_PROVIDER: %s\n' "$AI_PROVIDER_VALUE"
      ISSUES=$((ISSUES + 1))
      ;;
  esac
else
  echo "LLM disabled: AI provider settings not required"
fi

echo

if [[ -n "${TNS_ADMIN:-}" ]]; then
  if [[ -d "$TNS_ADMIN" ]]; then
    echo "Wallet directory exists: $TNS_ADMIN"
  else
    echo "MISSING: Wallet directory not found: $TNS_ADMIN"
    ISSUES=$((ISSUES + 1))
  fi
fi

echo

if (( ISSUES > 0 )); then
  echo "Environment check failed with $ISSUES issue(s)."
  exit 1
fi

echo "Environment check passed."
