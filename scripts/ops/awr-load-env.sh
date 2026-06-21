#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
ENV_FILE="$PROJECT_DIR/.env"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Project directory not found: $PROJECT_DIR" >&2
  return 1 2>/dev/null || exit 1
fi

if [[ ! -r "$ENV_FILE" ]]; then
  echo "Project environment file is not readable: $ENV_FILE" >&2
  return 1 2>/dev/null || exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

export AWRAI_PROJECT_DIR="$PROJECT_DIR"
echo "Loaded Agentic AI AWR Advisor environment from $ENV_FILE"
