#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/cloonix/pybackup"

# ── helpers ───────────────────────────────────────────────────────────────────
info() { printf '\033[1;34m::\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✔\033[0m  %s\n' "$*"; }
warn() { printf '\033[1;33m!\033[0m  %s\n' "$*"; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ── checks ────────────────────────────────────────────────────────────────────
command -v uv &>/dev/null || die "uv is required but not installed. See https://docs.astral.sh/uv/"

# ── install pybackup ──────────────────────────────────────────────────────────
info "Installing pybackup..."
uv tool install "git+${REPO}"
ok "pybackup installed"

UV_TOOL_BIN="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
if [[ ":$PATH:" != *":${UV_TOOL_BIN}:"* ]]; then
  warn "Add to your shell profile: export PATH=\"${UV_TOOL_BIN}:\$PATH\""
fi

# ── config ────────────────────────────────────────────────────────────────────
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pybackup"
CONFIG_FILE="$CONFIG_DIR/config.json"

if [[ -f "$CONFIG_FILE" ]]; then
  ok "Config already exists: $CONFIG_FILE"
else
  mkdir -p "$CONFIG_DIR"
  cat > "$CONFIG_FILE" <<'EOF'
{
  "default": "local",
  "destinations": [
    {
      "name": "local",
      "backend": "local",
      "path": "~/backups/pybackup"
    }
  ]
}
EOF
  ok "Starter config written to $CONFIG_FILE – edit it to add your destinations"
fi

printf '\n'
ok "Done. Run: pybackup -i /path/to/folder"
