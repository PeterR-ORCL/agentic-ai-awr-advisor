#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"
ISSUES=0

print_set() {
  local value="${1:-}"
  if [[ -n "$value" ]]; then
    printf 'set'
  else
    printf 'unset'
  fi
}

print_yes_no_dir() {
  local path="${1:-}"
  if [[ -n "$path" && -d "$path" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

print_yes_no_file() {
  local path="${1:-}"
  if [[ -n "$path" && -f "$path" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

kv() {
  local label="$1"
  local value="${2:-}"
  printf '  %-22s %s\n' "$label:" "${value:-unset}"
}

require_var() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    printf 'OK: %s\n' "$name"
  else
    printf 'MISSING: %s\n' "$name"
    ISSUES=$((ISSUES + 1))
  fi
}

present_var() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    printf 'present: %s\n' "$name"
  else
    printf 'absent: %s\n' "$name"
  fi
}

require_wallet_file() {
  local label="$1"
  local file_path="$2"
  if [[ -f "$file_path" ]]; then
    printf 'OK: %s\n' "$label"
  else
    printf 'MISSING: %s (%s)\n' "$label" "$file_path"
    ISSUES=$((ISSUES + 1))
  fi
}

load_env() {
  if [[ ! -d "$PROJECT_DIR" ]]; then
    printf 'Project directory not found: %s\n' "$PROJECT_DIR" >&2
    exit 1
  fi

  if [[ ! -r "$ENV_FILE" ]]; then
    printf 'Project environment file is not readable: %s\n' "$ENV_FILE" >&2
    exit 1
  fi

  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

tool_version() {
  local name="$1"
  local path
  path="$(command -v "$name" 2>/dev/null || true)"
  if [[ -z "$path" ]]; then
    printf 'version: missing'
    return 0
  fi

  case "$name" in
    sql)
      "$path" -version 2>&1 | head -n 1 || printf 'version unavailable'
      ;;
    oci)
      "$path" --version 2>&1 | head -n 1 || printf 'version unavailable'
      ;;
    *)
      "$path" --version 2>&1 | head -n 1 || printf 'version unavailable'
      ;;
  esac
}

tool_status() {
  local name="$1"
  local path
  path="$(command -v "$name" 2>/dev/null || true)"
  if [[ -n "$path" ]]; then
    printf 'OK: %s (%s) - %s\n' "$name" "$path" "$(tool_version "$name")"
  else
    printf 'MISSING: %s (missing) - version: missing\n' "$name"
    ISSUES=$((ISSUES + 1))
  fi
}

validate_wallet() {
  printf '\nWallet:\n'
  kv 'Wallet path' "${TNS_ADMIN:-unset}"
  kv 'Wallet exists' "$(print_yes_no_dir "${TNS_ADMIN:-}")"
  kv 'tnsnames.ora' "$(print_yes_no_file "${TNS_ADMIN:-}/tnsnames.ora")"
  kv 'sqlnet.ora' "$(print_yes_no_file "${TNS_ADMIN:-}/sqlnet.ora")"
  kv 'cwallet.sso' "$(print_yes_no_file "${TNS_ADMIN:-}/cwallet.sso")"

  if [[ -z "${TNS_ADMIN:-}" || ! -d "${TNS_ADMIN:-}" ]]; then
    ISSUES=$((ISSUES + 1))
    return
  fi

  require_wallet_file 'tnsnames.ora' "$TNS_ADMIN/tnsnames.ora"
  require_wallet_file 'sqlnet.ora' "$TNS_ADMIN/sqlnet.ora"
  require_wallet_file 'cwallet.sso' "$TNS_ADMIN/cwallet.sso"
}

validate_ai_provider() {
  printf '\nAI settings:\n'
  kv 'AI_PROVIDER' "${AI_PROVIDER:-unset}"
  kv 'USE_LLM' "${USE_LLM:-unset}"
  kv 'OCI_MODEL' "${OCI_MODEL:-unset}"
  kv 'OCI_MODEL_ID' "$(print_set "${OCI_MODEL_ID:-}")"
  kv 'OCI_COMPARTMENT_ID' "$(print_set "${OCI_COMPARTMENT_ID:-}")"
  kv 'OPENAI_MODEL' "${OPENAI_MODEL:-unset}"
  kv 'OPENAI_API_KEY' "$(print_set "${OPENAI_API_KEY:-}")"

  if [[ "${USE_LLM:-false}" != "true" && "${USE_LLM:-false}" != "1" && "${APP_MODE:-oracle}" != "full" ]]; then
    printf 'LLM validation skipped because USE_LLM is not true and APP_MODE is not full.\n'
    return
  fi

  printf '\nRequired AI settings:\n'
  require_var AI_PROVIDER

  case "${AI_PROVIDER:-}" in
    oci)
      require_var OCI_MODEL
      require_var OCI_MODEL_ID
      require_var OCI_COMPARTMENT_ID
      require_var OCI_CONFIG_FILE
      require_var OCI_CONFIG_PROFILE
      require_var OCI_REGION
      present_var OPENAI_MODEL
      present_var OPENAI_API_KEY
      ;;
    openai)
      require_var OPENAI_MODEL
      require_var OPENAI_API_KEY
      present_var OCI_MODEL
      present_var OCI_MODEL_ID
      present_var OCI_COMPARTMENT_ID
      ;;
    "")
      ;;
    *)
      printf 'INVALID: AI_PROVIDER must be oci or openai when LLM is enabled. Current value: %s\n' "${AI_PROVIDER:-}"
      ISSUES=$((ISSUES + 1))
      ;;
  esac
}

load_env
MODE="${APP_MODE:-oracle}"
CONNECT_MODE_VALUE="${CONNECT_MODE:-password}"

printf 'Agentic AWR environment check\n'
printf -- '-----------------------------\n'
printf 'Project:      %s\n' "$PROJECT_DIR"
printf 'Env file:     %s\n' "$ENV_FILE"
printf '\n'

printf 'Runtime:\n'
kv 'APP_MODE' "${APP_MODE:-unset}"
kv 'USE_OCI' "${USE_OCI:-unset}"
kv 'USE_LLM' "${USE_LLM:-unset}"
printf '\n'

case "$MODE" in
  mock)
    printf 'Mock mode: database, wallet, OCI, and AI provider settings are not required.\n'
    ;;
  oracle|full)
    printf 'Database:\n'
    kv 'ADB_USER' "${ADB_USER:-unset}"
    kv 'ADB_PASSWORD' "$(print_set "${ADB_PASSWORD:-}")"
    kv 'ADB_DSN' "${ADB_DSN:-unset}"
    kv 'CONNECT_MODE' "$CONNECT_MODE_VALUE"
    kv 'ADB_OCID' "$(print_set "${ADB_OCID:-}")"
    kv 'ADB_WALLET_ZIP' "$(print_set "${ADB_WALLET_ZIP:-}")"
    printf '\nRequired database settings:\n'
    require_var ADB_USER
    require_var ADB_DSN
    require_var TNS_ADMIN
    require_var OCI_REGION
    require_var ADB_OCID
    if [[ "$CONNECT_MODE_VALUE" == 'password' ]]; then
      require_var ADB_PASSWORD
    fi

    validate_wallet

    printf '\nOCI:\n'
    kv 'OCI_CONFIG_FILE' "${OCI_CONFIG_FILE:-$HOME/.oci/config}"
    kv 'OCI_CONFIG_PROFILE' "${OCI_CONFIG_PROFILE:-${OCI_PROFILE:-DEFAULT}}"
    kv 'OCI_REGION' "${OCI_REGION:-unset}"

    printf '\nObject Storage:\n'
    kv 'OCI_AWR_PREFIX' "$(print_set "${OCI_AWR_PREFIX:-}")"

    validate_ai_provider
    ;;
  *)
    printf 'INVALID: APP_MODE must be mock, oracle, or full. Current value: %s\n' "$MODE"
    ISSUES=$((ISSUES + 1))
    ;;
esac

printf '\nTool checks:\n'
tool_status sql
tool_status oci

printf '\n'
if (( ISSUES == 0 )); then
  printf 'Environment check passed.\n'
else
  printf 'Environment check failed with %d issue(s).\n' "$ISSUES"
  exit 1
fi
