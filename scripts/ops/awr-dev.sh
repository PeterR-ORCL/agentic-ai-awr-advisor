#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
cd "$PROJECT_DIR"

if [[ -r "$PROJECT_DIR/scripts/load-env.sh" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/scripts/load-env.sh"
fi

if [[ -r "$PROJECT_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.venv/bin/activate"
fi

echo "Agentic AI AWR Advisor dev helper"
echo "Project: $PROJECT_DIR"
echo

echo "Customize scripts/dev.sh for your project start command."
echo "Common examples:"
echo "  python app.py"
echo "  python -m streamlit run app.py"
echo "  uvicorn app.main:app --reload"
