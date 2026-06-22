#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="Agentic AI AWR Advisor"
PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
BRANCH="${AWRAI_BRANCH:-phase7-final-operational-certification}"
REMOTE="${AWRAI_REMOTE:-origin}"
REMOTE_REF="$REMOTE/$BRANCH"
EXPECTED_UNTRACKED_REGEX='^\?\? docs/forensics(/|$)'

TRACKED_SYNC_PATHS="
docs/architecture/project_shell_refactor.md
scripts/ops/awr-preflight.sh
scripts/ops/awr-db.sh
scripts/ops/awr-check-env.sh
scripts/ops/awr-sync-guard.sh
src/reporting/dashboard/product_handoff.py
src/reporting/dashboard/renderers/product_kit.py
tests/test_7reset_product_renderer_kit_contracts.py
tests/test_7reset_screen3_product_renderer_contracts.py
"

print_header() {
  local title="$1"
  printf '%s\n' "$title"
  printf '%*s\n' "${#title}" '' | tr ' ' '-'
}

die() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

safe_die() {
  printf '\n%s\n' "NOT safe to switch Macs." >&2
  die "$*"
}

cd_project() {
  cd "$PROJECT_DIR" || die "Project directory not found: $PROJECT_DIR"
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git worktree: $PROJECT_DIR"
}

phase7_check() {
  if [ -e PHASE7_COMPLETE ]; then
    safe_die "PHASE7_COMPLETE file exists. Stop."
  fi
  if git tag --list | grep -q 'PHASE7_COMPLETE'; then
    safe_die "PHASE7_COMPLETE tag exists. Stop."
  fi
  printf '%s\n' "PHASE7_COMPLETE file/tag absent"
}

assert_on_branch() {
  local current_branch
  current_branch="$(git branch --show-current)"
  [ "$current_branch" = "$BRANCH" ] || safe_die "Expected branch $BRANCH, got $current_branch"
}

assert_no_tracked_or_staged_diffs() {
  local tracked staged
  tracked="$(git diff --name-only)"
  staged="$(git diff --cached --name-only)"

  if [ -n "$tracked" ]; then
    printf '%s\n' "Tracked diffs present:" >&2
    printf '%s\n' "$tracked" >&2
    safe_die "Commit, restore, or inspect tracked diffs before leaving."
  fi

  if [ -n "$staged" ]; then
    printf '%s\n' "Staged files present:" >&2
    printf '%s\n' "$staged" >&2
    safe_die "Commit or unstage before leaving."
  fi
}

assert_only_expected_untracked() {
  local status unexpected
  status="$(git status --short)"

  if [ -z "$status" ]; then
    return 0
  fi

  unexpected="$(printf '%s\n' "$status" | grep -Ev "$EXPECTED_UNTRACKED_REGEX" || true)"
  if [ -n "$unexpected" ]; then
    printf '%s\n' "Unexpected dirty paths present:" >&2
    printf '%s\n' "$unexpected" >&2
    safe_die "Only docs/forensics/ may be untracked for this branch."
  fi
}

remote_exists() {
  git rev-parse --verify "$REMOTE_REF" >/dev/null 2>&1
}

ahead_behind_values() {
  if remote_exists; then
    git rev-list --left-right --count "$REMOTE_REF"...HEAD
  else
    printf 'unknown\tunknown\n'
  fi
}

print_ahead_behind() {
  local values behind ahead
  values="$(ahead_behind_values)"
  behind="$(printf '%s' "$values" | awk '{print $1}')"
  ahead="$(printf '%s' "$values" | awk '{print $2}')"

  printf '%s\n' "Ahead/behind vs $REMOTE_REF:"
  printf '%s\n' "$values"

  if [ "$behind" = "unknown" ] || [ "$ahead" = "unknown" ]; then
    printf '%s\n' "Remote status: remote ref unavailable."
  elif [ "$behind" = "0" ] && [ "$ahead" = "0" ]; then
    printf '%s\n' "Remote status: Everything up-to-date."
  elif [ "$behind" != "0" ] && [ "$ahead" = "0" ]; then
    printf '%s\n' "Remote status: Local branch is behind by $behind commit(s). Run awr-start first."
  elif [ "$behind" = "0" ] && [ "$ahead" != "0" ]; then
    printf '%s\n' "Remote status: Local branch is ahead by $ahead commit(s). Push required."
  else
    printf '%s\n' "Remote status: Branch has diverged. Manual Git review required."
  fi
}

behind_count() {
  local values
  values="$(ahead_behind_values)"
  printf '%s' "$values" | awk '{print $1}'
}

print_status_block() {
  local status
  status="$(git status --short)"
  if [ -n "$status" ]; then
    printf '%s\n' "$status"
  else
    printf '%s\n' "none"
  fi
}

show_status() {
  cd_project
  print_header "$PROJECT_NAME sync guard status"
  printf 'Project: %s\n' "$PWD"
  printf 'Branch:  %s\n' "$(git branch --show-current)"
  printf 'Expected branch: %s\n' "$BRANCH"
  printf 'Remote:  %s %s\n' "$REMOTE" "$(git remote get-url "$REMOTE" 2>/dev/null || printf 'unavailable')"
  printf 'Remote ref: %s\n' "$REMOTE_REF"
  print_ahead_behind
  printf '\nRecent commits:\n'
  git log --oneline -12
  printf '\nGit status:\n'
  print_status_block
  printf '\nTracked diff stat:\n'
  git diff --stat
  printf '\nTracked diff files:\n'
  git diff --name-only
  printf '\nStaged files:\n'
  git diff --cached --name-only
  printf '\n'
  phase7_check
}

before_leave() {
  cd_project
  print_header "$PROJECT_NAME before-leave guard"
  printf 'Project: %s\n' "$PWD"
  printf 'Branch:  %s\n' "$(git branch --show-current)"
  printf 'Remote:  %s\n' "$REMOTE_REF"
  printf '\n'

  assert_on_branch
  phase7_check

  printf '\nFetching %s with prune...\n' "$REMOTE"
  git fetch --all --prune

  assert_no_tracked_or_staged_diffs
  assert_only_expected_untracked

  printf '\nStatus before leaving active Mac:\n'
  print_status_block
  printf '\n'
  print_ahead_behind

  local behind
  behind="$(behind_count)"
  if [ "$behind" = "unknown" ]; then
    safe_die "Remote ref unavailable; cannot verify before leaving."
  fi
  if [ "$behind" != "0" ]; then
    safe_die "Local branch is behind $REMOTE_REF by $behind commit(s). Run awr-start first."
  fi

  printf '\nPushing %s to %s...\n' "$BRANCH" "$REMOTE"
  if ! git push "$REMOTE" "$BRANCH" 2>&1; then
    printf '\n%s\n' "NOT safe to switch Macs. Push failed."
    exit 1
  fi

  printf '\nVerifying remote alignment after push...\n'
  git fetch --all --prune >/dev/null 2>&1 || true
  print_ahead_behind

  local post_behind post_values post_ahead
  post_values="$(ahead_behind_values)"
  post_behind="$(printf '%s' "$post_values" | awk '{print $1}')"
  post_ahead="$(printf '%s' "$post_values" | awk '{print $2}')"
  if [ "$post_behind" = "0" ] && [ "$post_ahead" = "0" ]; then
    printf '\n%s\n' "Safe to switch Macs."
  else
    printf '\n%s\n' "NOT safe to switch Macs. Branch is not aligned after push."
    exit 1
  fi
}

before_start() {
  cd_project
  print_header "$PROJECT_NAME before-start guard"
  printf 'Project: %s\n' "$PWD"
  printf 'Branch:  %s\n' "$(git branch --show-current)"
  printf 'Remote:  %s\n' "$REMOTE_REF"
  printf '\n'

  assert_on_branch
  phase7_check
  assert_no_tracked_or_staged_diffs

  printf '\nFetching %s with prune...\n' "$REMOTE"
  git fetch --all --prune

  printf 'Pulling %s with fast-forward only...\n' "$REMOTE_REF"
  git pull --ff-only "$REMOTE" "$BRANCH"

  assert_no_tracked_or_staged_diffs
  assert_only_expected_untracked

  printf '\n'
  print_ahead_behind
  printf '\nStatus after start guard:\n'
  print_status_block
  printf '\n\n%s\n' "Ready for Codex."
}

repair_stale() {
  cd_project
  print_header "$PROJECT_NAME stale-sync repair"
  assert_on_branch
  phase7_check

  printf 'Fetching %s with prune...\n' "$REMOTE"
  git fetch --all --prune

  local stamp hold path
  stamp="$(date +%Y%m%d-%H%M%S)"
  hold="$HOME/Downloads/awr-unsynced-hold-$stamp"
  mkdir -p "$hold"

  printf 'Moving synced untracked copies to: %s\n' "$hold"

  for path in $TRACKED_SYNC_PATHS; do
    if [ -e "$path" ] && ! git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
      mkdir -p "$hold/$(dirname "$path")"
      mv "$path" "$hold/$path"
      printf 'moved: %s\n' "$path"
    fi
  done

  printf '\nPulling authoritative branch with fast-forward only...\n'
  git pull --ff-only "$REMOTE" "$BRANCH"

  assert_no_tracked_or_staged_diffs
  assert_only_expected_untracked
  printf '\nRepair complete. Hold folder kept at:\n%s\n' "$hold"
}

append_work_ready_issue() {
  local message="$1"
  if [ -n "${WORK_READY_ISSUES:-}" ]; then
    WORK_READY_ISSUES="${WORK_READY_ISSUES}
"
  fi
  WORK_READY_ISSUES="${WORK_READY_ISSUES}    - $message"
}

work_ready_evaluate() {
  local current tracked staged status unexpected values behind ahead
  current="$(git branch --show-current 2>/dev/null || true)"

  if [ "$current" != "$BRANCH" ]; then
    append_work_ready_issue "expected branch $BRANCH, got ${current:-unknown}"
  fi

  if [ -e PHASE7_COMPLETE ]; then
    append_work_ready_issue "PHASE7_COMPLETE file exists"
  fi

  if git tag --list | grep -q 'PHASE7_COMPLETE'; then
    append_work_ready_issue "PHASE7_COMPLETE tag exists"
  fi

  tracked="$(git diff --name-only)"
  if [ -n "$tracked" ]; then
    append_work_ready_issue "tracked diffs present; commit, restore, or inspect them before work"
  fi

  staged="$(git diff --cached --name-only)"
  if [ -n "$staged" ]; then
    append_work_ready_issue "staged files present; commit or unstage them before work"
  fi

  status="$(git status --short)"
  if [ -n "$status" ]; then
    unexpected="$(printf '%s\n' "$status" | grep -Ev "$EXPECTED_UNTRACKED_REGEX" || true)"
    if [ -n "$unexpected" ]; then
      append_work_ready_issue "unexpected dirty paths present; only docs/forensics/ may be untracked"
    fi
  fi

  if ! remote_exists; then
    append_work_ready_issue "remote ref unavailable: $REMOTE_REF"
  else
    values="$(ahead_behind_values)"
    behind="$(printf '%s' "$values" | awk '{print $1}')"
    ahead="$(printf '%s' "$values" | awk '{print $2}')"

    if [ "$behind" = "unknown" ] || [ "$ahead" = "unknown" ]; then
      append_work_ready_issue "remote alignment could not be determined"
    elif [ "$behind" != "0" ] && [ "$ahead" = "0" ]; then
      append_work_ready_issue "local branch is behind $REMOTE_REF by $behind commit(s); run awr-start"
    elif [ "$behind" = "0" ] && [ "$ahead" != "0" ]; then
      append_work_ready_issue "local branch is ahead of $REMOTE_REF by $ahead commit(s); run awr-leave"
    elif [ "$behind" != "0" ] && [ "$ahead" != "0" ]; then
      append_work_ready_issue "local branch has diverged from $REMOTE_REF; manual Git review required"
    fi
  fi

  [ -z "${WORK_READY_ISSUES:-}" ]
}

work_ready() {
  cd_project
  print_header "$PROJECT_NAME work readiness"
  printf 'Project: %s\n' "$PWD"
  printf 'Branch:  %s\n' "$(git branch --show-current 2>/dev/null || printf 'unknown')"
  printf 'Remote:  %s\n' "$REMOTE_REF"
  printf '\n'

  WORK_READY_ISSUES=""
  printf 'Refreshing %s with prune...\n' "$REMOTE"
  if ! git fetch --all --prune >/dev/null 2>&1; then
    append_work_ready_issue "unable to fetch remote refs from $REMOTE"
  fi

  work_ready_evaluate || true

  printf '\nGit status:\n'
  print_status_block
  printf '\nTracked diff files:\n'
  git diff --name-only
  printf '\nStaged files:\n'
  git diff --cached --name-only
  printf '\n'
  print_ahead_behind

  printf '\nWork safety:\n'
  if [ -z "${WORK_READY_ISSUES:-}" ]; then
    printf '  Safe to continue to work on %s.\n' "$PROJECT_NAME"
    return 0
  fi

  printf '  NOT safe to continue to work on %s.\n' "$PROJECT_NAME"
  printf '  Reasons:\n'
  printf '%s\n' "$WORK_READY_ISSUES"
  printf '  Next step:\n'
  printf '    Run awr-start if the branch is behind, awr-leave if only ahead, or inspect/commit/restore the listed changes.\n'
  return 1
}

usage() {
  cat <<USAGE
Usage:
  scripts/ops/awr-sync-guard.sh status
  scripts/ops/awr-sync-guard.sh before-leave
  scripts/ops/awr-sync-guard.sh before-start
  scripts/ops/awr-sync-guard.sh repair-stale
  scripts/ops/awr-sync-guard.sh work-ready

Environment overrides:
  AWRAI_PROJECT_DIR
  AWRAI_BRANCH
  AWRAI_REMOTE
USAGE
}

cmd="${1:-status}"
case "$cmd" in
  status)
    show_status
    ;;
  before-leave)
    before_leave
    ;;
  before-start)
    before_start
    ;;
  work-ready)
    work_ready
    ;;
  repair-stale)
    repair_stale
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    die "Unknown command: $cmd"
    ;;
esac
