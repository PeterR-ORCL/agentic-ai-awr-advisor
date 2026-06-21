#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="Agentic AI AWR Advisor"
PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="${AWRAI_ENV_FILE:-$PROJECT_DIR/.env}"
EXPECTED_BRANCH="${AWRAI_BRANCH:-phase7-final-operational-certification}"
REMOTE="${AWRAI_REMOTE:-origin}"
REMOTE_REF="$REMOTE/$EXPECTED_BRANCH"

line() {
  printf -- '----------------------------------------\n'
}

field() {
  local label="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    value="unset"
  fi
  printf '  %-24s %s\n' "$label:" "$value"
}

set_status() {
  local value="${1:-}"
  if [[ -n "$value" ]]; then
    printf 'set'
  else
    printf 'unset'
  fi
}

exists_status() {
  local path="${1:-}"
  if [[ -n "$path" && -e "$path" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

cmd_path() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    command -v "$name"
  else
    printf 'missing'
  fi
}

project_python() {
  if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    printf '%s' "$PROJECT_DIR/.venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    command -v python
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    printf 'missing'
  fi
}

project_pip() {
  if [[ -x "$PROJECT_DIR/.venv/bin/pip" ]]; then
    printf '%s' "$PROJECT_DIR/.venv/bin/pip"
  elif command -v pip >/dev/null 2>&1; then
    command -v pip
  elif command -v pip3 >/dev/null 2>&1; then
    command -v pip3
  else
    printf 'missing'
  fi
}

version_for_tool() {
  local label="$1"
  local path="$2"
  local version=""

  if [[ -z "$path" || "$path" == "missing" ]]; then
    printf 'version: missing'
    return 0
  fi

  case "$label" in
    git)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    python|python3)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    pip|pip3)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    node)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    npm)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    sql)
      version="$($path -V 2>&1 | head -n 1 || true)"
      ;;
    oci)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
    rclone)
      version="$($path version 2>&1 | head -n 1 || true)"
      ;;
    *)
      version="$($path --version 2>&1 | head -n 1 || true)"
      ;;
  esac

  if [[ -z "$version" ]]; then
    printf 'version: unavailable'
  else
    printf '%s' "$version"
  fi
}

tool_check() {
  local label="$1"
  local path="$2"
  local version

  if [[ -z "$path" || "$path" == "missing" ]]; then
    printf 'MISSING: %s (missing) - version: missing\n' "$label"
    return 0
  fi

  version="$(version_for_tool "$label" "$path")"
  printf 'OK: %s (%s) - %s\n' "$label" "$path" "$version"
}

print_command_or_none() {
  local output
  output="$($@ 2>/dev/null || true)"
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
  else
    printf '  none\n'
  fi
}

load_env() {
  if [[ ! -r "$ENV_FILE" ]]; then
    return 0
  fi

  local restore_allexport=0
  if [[ ! -o allexport ]]; then
    set -a
    restore_allexport=1
  fi

  # shellcheck disable=SC1090
  source "$ENV_FILE"

  if (( restore_allexport )); then
    set +a
  fi
}

if [[ ! -d "$PROJECT_DIR" ]]; then
  printf 'Project directory not found: %s\n' "$PROJECT_DIR" >&2
  exit 1
fi

cd "$PROJECT_DIR"
load_env

PYTHON_CMD="$(project_python)"
PIP_CMD="$(project_pip)"
CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"

printf '%s preflight\n' "$PROJECT_NAME"
line

printf 'Project\n'
field 'Project dir' "$PROJECT_DIR"
field 'Env file' "$ENV_FILE"
field 'Env file readable' "$(exists_status "$ENV_FILE")"
field 'Expected branch' "$EXPECTED_BRANCH"
printf '\n'

printf 'Git\n'
field 'Branch' "$CURRENT_BRANCH"
field 'Remote' "$REMOTE"
field 'Remote ref' "$REMOTE_REF"
if git rev-parse --verify "$REMOTE_REF" >/dev/null 2>&1; then
  field 'Ahead/behind' "$(git rev-list --left-right --count "$REMOTE_REF"...HEAD 2>/dev/null || printf 'unavailable')"
else
  field 'Ahead/behind' 'remote ref unavailable'
fi
printf '\nRecent commits:\n'
print_command_or_none git log --oneline -12
printf '\nGit status:\n'
print_command_or_none git status --short
printf '\nTracked diff stat:\n'
print_command_or_none git diff --stat
printf '\nTracked diff files:\n'
print_command_or_none git diff --name-only
printf '\nStaged files:\n'
print_command_or_none git diff --cached --name-only
printf '\n'

printf 'Environment\n'
field 'APP_MODE' "${APP_MODE:-unset}"
field 'USE_OCI' "${USE_OCI:-unset}"
field 'USE_LLM' "${USE_LLM:-unset}"
field 'ADB_USER' "${ADB_USER:-unset}"
field 'ADB_DSN' "${ADB_DSN:-unset}"
field 'TNS_ADMIN' "${TNS_ADMIN:-unset}"
field 'TNS_ADMIN exists' "$(exists_status "${TNS_ADMIN:-}")"
field 'OCI_REGION' "${OCI_REGION:-unset}"
field 'ADB_OCID' "$(set_status "${ADB_OCID:-}")"
field 'OCI_CONFIG_FILE' "$(set_status "${OCI_CONFIG_FILE:-}")"
field 'OCI_CONFIG_PROFILE' "${OCI_CONFIG_PROFILE:-${OCI_PROFILE:-unset}}"
field 'OCI_AWR_PREFIX' "$(set_status "${OCI_AWR_PREFIX:-}")"
printf '\n'

printf 'AI settings\n'
field 'AI_PROVIDER' "${AI_PROVIDER:-unset}"
field 'OCI_MODEL' "${OCI_MODEL:-unset}"
field 'OCI_MODEL_ID' "$(set_status "${OCI_MODEL_ID:-}")"
field 'OCI_COMPARTMENT_ID' "$(set_status "${OCI_COMPARTMENT_ID:-}")"
field 'OPENAI_MODEL' "${OPENAI_MODEL:-unset}"
field 'OPENAI_API_KEY' "$(set_status "${OPENAI_API_KEY:-}")"
printf '\n'

printf 'Wallet\n'
field 'Wallet path (TNS_ADMIN)' "${TNS_ADMIN:-unset}"
field 'Wallet directory exists' "$(exists_status "${TNS_ADMIN:-}")"
field 'tnsnames.ora' "$(exists_status "${TNS_ADMIN:-}/tnsnames.ora")"
field 'sqlnet.ora' "$(exists_status "${TNS_ADMIN:-}/sqlnet.ora")"
field 'cwallet.sso' "$(exists_status "${TNS_ADMIN:-}/cwallet.sso")"
printf '\n'

printf 'Tool checks:\n'
tool_check git "$(cmd_path git)"
tool_check python "$PYTHON_CMD"
tool_check python3 "$(cmd_path python3)"
tool_check pip "$PIP_CMD"
tool_check pip3 "$(cmd_path pip3)"
tool_check node "$(cmd_path node)"
tool_check npm "$(cmd_path npm)"
tool_check sql "$(cmd_path sql)"
tool_check oci "$(cmd_path oci)"
tool_check rclone "$(cmd_path rclone)"
printf '\n'

printf 'Project markers\n'
if [[ -e PHASE7_COMPLETE ]]; then
  field 'PHASE7_COMPLETE file' 'EXISTS'
else
  field 'PHASE7_COMPLETE file' 'absent'
fi
if git tag --list | grep -q 'PHASE7_COMPLETE'; then
  field 'PHASE7_COMPLETE tag' 'EXISTS'
else
  field 'PHASE7_COMPLETE tag' 'absent'
fi
