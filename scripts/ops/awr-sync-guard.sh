#!/usr/bin/env bash
# AWR two-Mac Git sync guard.
#
# Rule enforced by this script:
#   Folder sync is convenience. Git is project authority.
#
# Commands:
#   status        Show current branch/status/PHASE7 state.
#   before-leave  Verify safe state and push before switching Macs.
#   before-start  Fetch/pull fast-forward and verify safe state before work.
#   repair-stale  Move untracked file-sync copies aside, then pull Git truth.
#
# This script does not run Codex, tests, analysis, dashboard regeneration,
# commits, tags, or PHASE7_COMPLETE actions.

set -euo pipefail

PROJECT_DIR="${AWRAI_PROJECT_DIR:-$HOME/Projects/agentic-ai-awr-advisor}"
BRANCH="${AWRAI_BRANCH:-phase7-final-operational-certification}"
REMOTE="${AWRAI_REMOTE:-origin}"
REMOTE_REF="$REMOTE/$BRANCH"
EXPECTED_UNTRACKED_REGEX='^(\?\? docs/forensics(/|$))'

usage() {
  cat <<USAGE
Usage:
  scripts/ops/awr-sync-guard.sh status
  scripts/ops/awr-sync-guard.sh before-leave
  scripts/ops/awr-sync-guard.sh before-start
  scripts/ops/awr-sync-guard.sh repair-stale

Environment overrides:
  AWRAI_PROJECT_DIR   Default: \$HOME/Projects/agentic-ai-awr-advisor
  AWRAI_BRANCH        Default: phase7-final-operational-certification
  AWRAI_REMOTE        Default: origin

Notes:
  - Folder sync is convenience; Git is project authority.
  - Expected normal recovery status is only: ?? docs/forensics/
  - If stale synced files appear untracked, run: repair-stale
USAGE
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

cd_project() {
  cd "$PROJECT_DIR" || die "Project directory not found: $PROJECT_DIR"
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git worktree: $PROJECT_DIR"
}

current_branch() {
  git branch --show-current 2>/dev/null || true
}

assert_on_branch() {
  branch="$(current_branch)"
  [ "$branch" = "$BRANCH" ] || die "Expected branch $BRANCH, got ${branch:-unknown}"
}

phase7_check() {
  if [ -e PHASE7_COMPLETE ]; then
    die "PHASE7_COMPLETE file exists. Stop."
  fi

  if git tag --list | grep -q 'PHASE7_COMPLETE'; then
    die "PHASE7_COMPLETE tag exists. Stop."
  fi

  printf '%s\n' "PHASE7_COMPLETE file/tag absent"
}

assert_no_tracked_or_staged_diffs() {
  if ! git diff --quiet; then
    printf '%s\n' "Tracked diff files:" >&2
    git diff --name-only >&2
    die "Tracked diffs present. Commit/revert before switching Macs."
  fi

  if ! git diff --cached --quiet; then
    printf '%s\n' "Staged files:" >&2
    git diff --cached --name-only >&2
    die "Staged files present. Commit/unstage before switching Macs."
  fi
}

unexpected_status_lines() {
  git status --short | grep -Ev "$EXPECTED_UNTRACKED_REGEX" || true
}

assert_only_expected_untracked() {
  unexpected="$(unexpected_status_lines)"
  if [ -n "$unexpected" ]; then
    printf '%s\n' "$unexpected" >&2
    die "Unexpected untracked/dirty paths present. Stop before Codex. If these are stale synced copies, run repair-stale."
  fi
}

fetch_remote() {
  git fetch --all --prune
}

assert_remote_exists() {
  fetch_remote
  git rev-parse --verify "$REMOTE_REF" >/dev/null 2>&1 || die "Remote branch missing: $REMOTE_REF"
}

show_ahead_behind() {
  if git rev-parse --verify "$REMOTE_REF" >/dev/null 2>&1; then
    printf '%s\n' "Ahead/behind vs $REMOTE_REF:"
    git rev-list --left-right --count "$REMOTE_REF"...HEAD
  else
    printf '%s\n' "Remote ref not available yet: $REMOTE_REF"
  fi
}

show_status() {
  cd_project

  printf '%s\n' "Project: $PWD"
  printf '%s\n' "Branch: $(current_branch)"
  printf '%s\n' "Remote: $REMOTE"
  printf '%s\n' "Remote ref: $REMOTE_REF"
  printf '%s\n' ""

  printf '%s\n' "Recent commits:"
  git log --oneline -12
  printf '%s\n' ""

  printf '%s\n' "Git status:"
  git status --short
  printf '%s\n' ""

  printf '%s\n' "Tracked diff stat:"
  git diff --stat
  printf '%s\n' ""

  printf '%s\n' "Tracked diff files:"
  git diff --name-only
  printf '%s\n' ""

  printf '%s\n' "Staged files:"
  git diff --cached --name-only
  printf '%s\n' ""

  if git rev-parse --verify "$REMOTE_REF" >/dev/null 2>&1; then
    show_ahead_behind
    printf '%s\n' ""
  fi

  phase7_check
}

before_leave() {
  cd_project
  assert_on_branch
  assert_no_tracked_or_staged_diffs
  phase7_check

  fetch_remote

  printf '%s\n' "Status before leaving active Mac:"
  git status --short
  printf '%s\n' ""

  assert_only_expected_untracked

  show_ahead_behind
  printf '%s\n' ""

  printf '%s\n' "Pushing $BRANCH to $REMOTE..."
  git push -u "$REMOTE" "$BRANCH"

  printf '%s\n' ""
  printf '%s\n' "Safe to switch Macs."
}

before_start() {
  cd_project
  assert_on_branch
  assert_no_tracked_or_staged_diffs
  phase7_check

  # Do not pull over unexpected file-sync residue. Repair first.
  assert_only_expected_untracked

  assert_remote_exists

  printf '%s\n' "Pulling authoritative branch with fast-forward only..."
  git pull --ff-only "$REMOTE" "$BRANCH"

  assert_no_tracked_or_staged_diffs
  assert_only_expected_untracked
  phase7_check

  printf '%s\n' ""
  printf '%s\n' "Ready for Codex. Expected state confirmed:"
  git status --short
}

move_if_untracked_remote_file() {
  path="$1"
  hold="$2"

  [ -e "$path" ] || return 0

  if git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    return 0
  fi

  mkdir -p "$hold/$(dirname "$path")"
  mv "$path" "$hold/$path"
  printf '%s\n' "$path"
}

repair_stale() {
  cd_project
  assert_on_branch
  assert_no_tracked_or_staged_diffs
  phase7_check
  assert_remote_exists

  stamp="$(date +%Y%m%d-%H%M%S)"
  hold="$HOME/Downloads/awr-unsynced-hold-$stamp"
  mkdir -p "$hold"
  moved_log="$hold/.moved_paths"
  : > "$moved_log"

  printf '%s\n' "Moving untracked synced copies that conflict with $REMOTE_REF to:"
  printf '%s\n' "$hold"
  printf '%s\n' ""

  git ls-tree -r --name-only "$REMOTE_REF" | while IFS= read -r path; do
    [ -n "$path" ] || continue
    moved_path="$(move_if_untracked_remote_file "$path" "$hold" || true)"
    if [ -n "$moved_path" ]; then
      printf '%s\n' "moved: $moved_path"
      printf '%s\n' "$moved_path" >> "$moved_log"
    fi
  done

  if [ ! -s "$moved_log" ]; then
    printf '%s\n' "No untracked copies of remote-tracked files were moved."
  fi

  printf '%s\n' ""
  printf '%s\n' "Fast-forwarding from $REMOTE_REF..."
  git pull --ff-only "$REMOTE" "$BRANCH"

  assert_no_tracked_or_staged_diffs
  assert_only_expected_untracked
  phase7_check

  printf '%s\n' ""
  printf '%s\n' "Repair complete. Hold folder kept at:"
  printf '%s\n' "$hold"
  printf '%s\n' ""
  printf '%s\n' "Current status:"
  git status --short
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
