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

connect_mode() {
  if [[ -n "${ADB_DB_CONNECT_MODE:-}" ]]; then
    printf '%s\n' "$ADB_DB_CONNECT_MODE"
  elif [[ -n "${AWR_DB_CONNECT_MODE:-}" ]]; then
    printf '%s\n' "$AWR_DB_CONNECT_MODE"
  else
    printf '%s\n' "prompt"
  fi
}

build_oci_args_array() {
  OCI_ARGS=()
  [[ -n "${OCI_CONFIG_FILE:-}" ]] && OCI_ARGS+=(--config-file "$OCI_CONFIG_FILE")
  [[ -n "${OCI_CONFIG_PROFILE:-}" ]] && OCI_ARGS+=(--profile "$OCI_CONFIG_PROFILE")
  [[ -n "${OCI_REGION:-}" ]] && OCI_ARGS+=(--region "$OCI_REGION")
}

show_env() {
  echo "Agentic AWR database environment"
  echo "--------------------------------"
  echo "Project:      $PROJECT_DIR"
  echo "Env file:     $ENV_FILE"
  echo "APP_MODE:     ${APP_MODE:-unset}"
  echo "ADB_USER:     ${ADB_USER:-unset}"
  if [[ -n "${ADB_PASSWORD:-}" ]]; then
    echo "ADB_PASSWORD: set"
  else
    echo "ADB_PASSWORD: unset"
  fi
  echo "ADB_DSN:      ${ADB_DSN:-unset}"
  echo "TNS_ADMIN:    ${TNS_ADMIN:-unset}"
  if [[ -n "${TNS_ADMIN:-}" && -d "${TNS_ADMIN:-}" ]]; then
    echo "TNS exists:   yes"
  else
    echo "TNS exists:   no"
  fi
  echo "ADB_WALLET_ZIP: ${ADB_WALLET_ZIP:-unset}"
  if [[ -n "${ADB_OCID:-}" ]]; then
    echo "ADB_OCID:     set"
  else
    echo "ADB_OCID:     unset"
  fi
  echo "OCI_CONFIG_FILE: ${OCI_CONFIG_FILE:-unset}"
  echo "OCI_CONFIG_PROFILE: ${OCI_CONFIG_PROFILE:-unset}"
  echo "OCI_REGION:   ${OCI_REGION:-unset}"
  if [[ -n "${OCI_AWR_PREFIX:-}" ]]; then
    echo "OCI_AWR_PREFIX: set"
  else
    echo "OCI_AWR_PREFIX: unset"
  fi
  echo "CONNECT_MODE: $(connect_mode)"
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
