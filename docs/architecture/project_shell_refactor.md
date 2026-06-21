# Agentic AI AWR Advisor shell setup

Keep `~/.zshrc` thin. Put the project logic in scripts that live with the project.

Add only these launchers to `~/.zshrc`:

```zsh
####################################
# Agentic AI AWR Advisor project
####################################
if (( ! ${+AWRAI_PROJECT_DIR} )); then
  typeset -g AWRAI_PROJECT_DIR="$HOME/Projects/agentic-ai-awr-advisor"
fi

awr-project() {
  "$AWRAI_PROJECT_DIR/scripts/project-shell.sh"
}

awr-preflight() {
  "$AWRAI_PROJECT_DIR/scripts/preflight.sh"
}

awrdb() {
  "$AWRAI_PROJECT_DIR/scripts/db.sh" "$@"
}

awr-obj() {
  "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" "$@"
}

# Optional compatibility aliases for the older helpers.
awr-ls() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" ls "$@"; }
awr-push() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" push "$@"; }
awr-sync() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" sync "$@"; }
awr-sync-dry() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" sync-dry "$@"; }
awr-clean() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" clean "$@"; }
awr-put() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" put "$@"; }
awr-del() { "$AWRAI_PROJECT_DIR/scripts/object-storage.sh" del "$@"; }
```

Then reload your shell:

```bash
source ~/.zshrc
```

## Commands

```bash
awr-preflight
awrdb env
awrdb status
awrdb connect
awr-project
awr-obj ls
```

## Notes

- Secrets remain in `~/Projects/agentic-ai-awr-advisor/.env`.
- Wallets should stay outside Git, preferably under `$HOME/adb_wallets/awrai`.
- These scripts do not read from the BankIQ project.
- `awrdb connect` does not pass the database password on the command line.
