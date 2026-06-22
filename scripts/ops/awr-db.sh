#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"
OCI_ARGS=()

usage() {
  cat <<'USAGE'
Usage: awrdb <command>

Commands:
  connect      Connect to the AWR Autonomous Database with SQLcl
  env          Show sanitized database environment
  status       Show Autonomous Database lifecycle status
  start        Start the Autonomous Database
  stop         Stop the Autonomous Database
  help         Show this help

Connection modes:
  ADB_DB_CONNECT_MODE=prompt       Prompt for password in SQLcl
  ADB_DB_CONNECT_MODE=password     Use ADB_PASSWORD from .env
  ADB_DB_CONNECT_MODE=cloudconfig  Use ADB_WALLET_ZIP with SQLcl -cloudconfig

AWR-specific fallback:
  AWR_DB_CONNECT_MODE may be used when ADB_DB_CONNECT_MODE is unset.
USAGE
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed or is not in PATH."
}

require_env() {
  local name value
  for name in "$@"; do
    eval "value=\${$name:-}"
    [[ -n "$value" ]] || fail "Required project setting is missing: $name"
  done
}

load_env() {
  [[ -d "$PROJECT_DIR" ]] || fail "Project directory not found: $PROJECT_DIR"
  [[ -r "$ENV_FILE" ]] || fail "Project environment file is not readable: $ENV_FILE"

  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a

  [[ -n "${TNS_ADMIN:-}" ]] && export TNS_ADMIN
}

mask_set() {
  local value="${1:-}"
  if [[ -n "$value" ]]; then
    printf 'set'
  else
    printf 'unset'
  fi
}

yes_no_dir() {
  local path="${1:-}"
  if [[ -n "$path" && -d "$path" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

yes_no_file() {
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
  printf '  %-21s %s\n' "$label:" "${value:-unset}"
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
  fi
}

connect_mode() {
  if [[ -n "${ADB_DB_CONNECT_MODE:-}" ]]; then
    printf '%s\n' "$ADB_DB_CONNECT_MODE"
  elif [[ -n "${AWR_DB_CONNECT_MODE:-}" ]]; then
    printf '%s\n' "$AWR_DB_CONNECT_MODE"
  else
    printf '%s\n' "prompt"
  fi
}

oci_profile_value() {
  printf '%s\n' "${OCI_CONFIG_PROFILE:-${OCI_PROFILE:-}}"
}

build_oci_args_array() {
  OCI_ARGS=()
  local profile
  profile="$(oci_profile_value)"
  [[ -n "${OCI_CONFIG_FILE:-}" ]] && OCI_ARGS+=(--config-file "$OCI_CONFIG_FILE")
  [[ -n "$profile" ]] && OCI_ARGS+=(--profile "$profile")
  [[ -n "${OCI_REGION:-}" ]] && OCI_ARGS+=(--region "$OCI_REGION")
}

show_env() {
  echo "Agentic AWR database environment"
  echo "--------------------------------"
  echo "Project:      $PROJECT_DIR"
  echo "Env file:     $ENV_FILE"
  echo

  echo "Runtime:"
  kv "APP_MODE" "${APP_MODE:-unset}"
  kv "USE_OCI" "${USE_OCI:-unset}"
  kv "USE_LLM" "${USE_LLM:-unset}"
  echo

  echo "Database:"
  kv "ADB_USER" "${ADB_USER:-unset}"
  kv "ADB_PASSWORD" "$(mask_set "${ADB_PASSWORD:-}")"
  kv "ADB_DSN" "${ADB_DSN:-unset}"
  kv "CONNECT_MODE" "$(connect_mode)"
  kv "ADB_OCID" "$(mask_set "${ADB_OCID:-}")"
  kv "ADB_WALLET_ZIP" "$(mask_set "${ADB_WALLET_ZIP:-}")"
  echo

  echo "Wallet:"
  kv "Wallet path" "${TNS_ADMIN:-unset}"
  kv "Wallet exists" "$(yes_no_dir "${TNS_ADMIN:-}")"
  kv "tnsnames.ora" "$(yes_no_file "${TNS_ADMIN:-}/tnsnames.ora")"
  kv "sqlnet.ora" "$(yes_no_file "${TNS_ADMIN:-}/sqlnet.ora")"
  kv "cwallet.sso" "$(yes_no_file "${TNS_ADMIN:-}/cwallet.sso")"
  echo

  echo "OCI:"
  kv "OCI_CONFIG_FILE" "${OCI_CONFIG_FILE:-unset}"
  kv "OCI_CONFIG_PROFILE" "${OCI_CONFIG_PROFILE:-${OCI_PROFILE:-unset}}"
  kv "OCI_REGION" "${OCI_REGION:-unset}"
  echo

  echo "Project-specific:"
  kv "OCI_AWR_PREFIX" "$(mask_set "${OCI_AWR_PREFIX:-}")"
  echo

  echo "Tool checks:"
  tool_status sql
  tool_status oci
}

connect_db() {
  require_cmd sql
  require_env ADB_USER ADB_DSN TNS_ADMIN

  local mode
  mode="$(connect_mode)"

  case "$mode" in
    prompt)
      sql -L "${ADB_USER}@${ADB_DSN}"
      ;;
    password)
      require_env ADB_PASSWORD
      sql -L "${ADB_USER}/${ADB_PASSWORD}@${ADB_DSN}"
      ;;
    cloudconfig)
      require_env ADB_WALLET_ZIP
      if [[ -n "${ADB_PASSWORD:-}" ]]; then
        sql -L -cloudconfig "$ADB_WALLET_ZIP" "${ADB_USER}/${ADB_PASSWORD}@${ADB_DSN}"
      else
        sql -L -cloudconfig "$ADB_WALLET_ZIP" "${ADB_USER}@${ADB_DSN}"
      fi
      ;;
    *)
      fail "Unsupported ADB_DB_CONNECT_MODE: $mode"
      ;;
  esac
}

adb_status() {
  require_cmd oci
  require_env ADB_OCID OCI_REGION
  build_oci_args_array
  oci "${OCI_ARGS[@]}" db autonomous-database get \
    --autonomous-database-id "$ADB_OCID" \
    --query 'data."lifecycle-state"' \
    --raw-output
}

adb_start() {
  require_cmd oci
  require_env ADB_OCID OCI_REGION
  build_oci_args_array
  echo "Starting AWR Autonomous Database..."
  oci "${OCI_ARGS[@]}" db autonomous-database start \
    --autonomous-database-id "$ADB_OCID" \
    --wait-for-state AVAILABLE \
    >/dev/null
  echo "AWR Autonomous Database is AVAILABLE."
}

adb_stop() {
  require_cmd oci
  require_env ADB_OCID OCI_REGION
  build_oci_args_array
  echo "Stopping AWR Autonomous Database..."
  oci "${OCI_ARGS[@]}" db autonomous-database stop \
    --autonomous-database-id "$ADB_OCID" \
    --wait-for-state STOPPED \
    >/dev/null
  echo "AWR Autonomous Database is STOPPED."
}

action="${1:-help}"
shift || true

case "$action" in
  help|-h|--help)
    usage
    ;;
  env)
    load_env
    show_env
    ;;
  connect)
    load_env
    connect_db
    ;;
  status)
    load_env
    adb_status
    ;;
  start)
    load_env
    adb_start
    ;;
  stop)
    load_env
    adb_stop
    ;;
  *)
    echo "Unknown command: $action" >&2
    echo >&2
    usage >&2
    exit 1
    ;;
esac
