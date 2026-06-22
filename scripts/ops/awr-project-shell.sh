#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"

if [[ "${BANKIQ_PROJECT_ACTIVE:-0}" == "1" ]]; then
  echo "Already inside the BankIQ AI project shell. Run 'exit' first." >&2
  exit 1
fi

if [[ "${AWRAI_PROJECT_ACTIVE:-0}" == "1" ]]; then
  echo "Already inside the Agentic AI AWR Advisor project shell."
  exit 0
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Agentic AI AWR Advisor project directory not found: $PROJECT_DIR" >&2
  exit 1
fi

if [[ ! -r "$ENV_FILE" ]]; then
  echo "Agentic AI AWR Advisor .env file not found or not readable: $ENV_FILE" >&2
  exit 1
fi

cd "$PROJECT_DIR"

# Load all .env assignments into the environment so the child shell inherits them.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# Activate project virtual environment if present.
if [[ -r "$PROJECT_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.venv/bin/activate"
elif [[ -r "$PROJECT_DIR/backend/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/backend/.venv/bin/activate"
fi

export AWRAI_PROJECT_ACTIVE=1

value_or_unset() {
  local value="${1:-}"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
  else
    printf 'unset'
  fi
}

bool_from_env_or_db_presence() {
  local explicit="${USE_ORACLE:-${USE_ORACLE_DB:-}}"
  if [[ -n "$explicit" ]]; then
    printf '%s' "$explicit"
  elif [[ -n "${ADB_USER:-}" && -n "${ADB_DSN:-}" && -n "${TNS_ADMIN:-}" ]]; then
    printf 'true'
  else
    printf 'false'
  fi
}

object_storage_state() {
  if [[ -n "${OCI_AWR_PREFIX:-}" ]]; then
    printf 'enabled'
  else
    printf 'disabled'
  fi
}

PYTHON_BIN=""
PYTHON_VERSION="unavailable"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
  PYTHON_VERSION="$($PYTHON_BIN --version 2>&1 || echo unavailable)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
  PYTHON_VERSION="$($PYTHON_BIN --version 2>&1 || echo unavailable)"
fi

NODE_VERSION="unavailable"
if command -v node >/dev/null 2>&1; then
  NODE_VERSION="$(node --version 2>/dev/null || echo unavailable)"
fi

GIT_BRANCH="unavailable"
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_BRANCH="$(git branch --show-current 2>/dev/null || echo unavailable)"
fi

echo "Agentic AI AWR Advisor project shell is ready."
echo "Project: $PROJECT_DIR"
echo "Mode: $(value_or_unset "${APP_MODE:-}")"
echo "Use Oracle DB: $(bool_from_env_or_db_presence)"
echo "Use OCI: $(value_or_unset "${USE_OCI:-}")"
echo "Use LLM: $(value_or_unset "${USE_LLM:-}")"
echo "AI Provider: $(value_or_unset "${AI_PROVIDER:-}")"
echo "Object Storage: $(object_storage_state)"

if [[ -n "$PYTHON_BIN" ]]; then
  echo "Python path: $PYTHON_BIN"
  echo "Python version: $PYTHON_VERSION"
else
  echo "Python path: unavailable"
  echo "Python version: unavailable"
fi

echo "Node: $NODE_VERSION"
echo "Branch: $GIT_BRANCH"

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Git status:"
  git status --short
else
  echo "Git status: unavailable"
fi

echo "Run 'exit' to leave this isolated project environment."
echo


SYNC_GUARD="$PROJECT_DIR/scripts/ops/awr-sync-guard.sh"
if [[ -x "$SYNC_GUARD" ]]; then
  echo
  "$SYNC_GUARD" work-ready
else
  echo
  echo "Work safety:"
  echo "  NOT safe to continue to work on Agentic AI AWR Advisor."
  echo "  Reasons:"
  echo "    - sync guard is not executable or not found: $SYNC_GUARD"
  exit 1
fi

exec "${SHELL:-/bin/zsh}" -i
