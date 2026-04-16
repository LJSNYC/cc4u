#!/usr/bin/env bash
# ============================================================================
# CC4U — Install Script
# Claude Code 4 You: enhanced tmux sidebar for Claude Code
# ============================================================================
set -euo pipefail

# ── colour helpers ────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  C_GRN="\033[32m"; C_RED="\033[31m"; C_YEL="\033[33m"
  C_CYN="\033[36m"; C_BLD="\033[1m";  C_RST="\033[0m"
else
  C_GRN=""; C_RED=""; C_YEL=""; C_CYN=""; C_BLD=""; C_RST=""
fi

ok()   { echo -e "${C_GRN}✓${C_RST} $*"; }
err()  { echo -e "${C_RED}✗${C_RST} $*" >&2; }
info() { echo -e "${C_CYN}→${C_RST} $*"; }
warn() { echo -e "${C_YEL}⚠${C_RST} $*"; }
hdr()  { echo -e "\n${C_BLD}$*${C_RST}"; }
die()  { err "$*"; exit 1; }

# ── resolve project root ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

hdr "CC4U Installer"
echo "Project root: $PROJECT_ROOT"
echo

# ── OS detection ──────────────────────────────────────────────────────────────
hdr "Detecting operating system…"

OS=""
DISTRO=""
PKG_MGR=""

case "$(uname -s)" in
  Darwin)
    OS="macos"
    PKG_MGR="brew"
    ;;
  Linux)
    OS="linux"
    if command -v apt-get &>/dev/null; then
      DISTRO="debian"
      PKG_MGR="apt"
    elif command -v dnf &>/dev/null; then
      DISTRO="fedora"
      PKG_MGR="dnf"
    elif command -v pacman &>/dev/null; then
      DISTRO="arch"
      PKG_MGR="pacman"
    elif command -v zypper &>/dev/null; then
      DISTRO="suse"
      PKG_MGR="zypper"
    else
      DISTRO="unknown"
      PKG_MGR=""
    fi
    ;;
  *)
    die "Unsupported operating system: $(uname -s)"
    ;;
esac

if [[ "$OS" == "macos" ]]; then
  ok "macOS detected"
else
  ok "Linux/$DISTRO detected (package manager: ${PKG_MGR:-none found})"
fi

# ── install helper functions ──────────────────────────────────────────────────

pkg_install() {
  local pkg="$1"
  case "$PKG_MGR" in
    brew)   brew install "$pkg" ;;
    apt)    sudo apt-get install -y "$pkg" ;;
    dnf)    sudo dnf install -y "$pkg" ;;
    pacman) sudo pacman -S --noconfirm "$pkg" ;;
    zypper) sudo zypper install -y "$pkg" ;;
    *)      warn "Cannot auto-install '$pkg'; no known package manager."; return 1 ;;
  esac
}

version_gte() {
  # version_gte "actual_ver" "min_ver"  → 0 if actual >= min
  local IFS=.
  local -a ver=($1) min=($2)
  local i
  for (( i=0; i<${#min[@]}; i++ )); do
    local v="${ver[$i]:-0}"
    local m="${min[$i]:-0}"
    (( v > m )) && return 0
    (( v < m )) && return 1
  done
  return 0
}

# ── find best Python ──────────────────────────────────────────────────────────
# macOS ships Python 3.9 at /usr/bin/python3; prefer Homebrew or newer.
find_python3() {
  local candidates=("python3.13" "python3.12" "python3.11" "python3.10" "python3")
  local search_dirs=("/opt/homebrew/bin" "/usr/local/bin" "$HOME/.local/bin")
  # Check explicit paths first
  for d in "${search_dirs[@]}"; do
    for c in "${candidates[@]}"; do
      if [[ -x "$d/$c" ]]; then
        local ver
        ver="$("$d/$c" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)"
        if [[ -n "$ver" ]] && version_gte "$ver" "3.10"; then
          echo "$d/$c"
          return 0
        fi
      fi
    done
  done
  # Fall back to PATH lookup
  for c in "${candidates[@]}"; do
    if command -v "$c" &>/dev/null; then
      local ver
      ver="$("$c" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)"
      if [[ -n "$ver" ]] && version_gte "$ver" "3.10"; then
        command -v "$c"
        return 0
      fi
    fi
  done
  return 1
}

# ── dependency checks ─────────────────────────────────────────────────────────
hdr "Checking dependencies…"

MISSING=()

check_dep() {
  local cmd="$1"
  local min_ver="${2:-}"
  local pkg="${3:-$cmd}"
  local ver_flag="${4:---version}"

  if ! command -v "$cmd" &>/dev/null; then
    err "$cmd — not found"
    MISSING+=("$pkg")
    return 1
  fi

  if [[ -n "$min_ver" ]]; then
    local actual
    actual="$("$cmd" $ver_flag 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true)"
    if [[ -z "$actual" ]]; then
      warn "$cmd — cannot determine version (continuing)"
    elif version_gte "$actual" "$min_ver"; then
      ok "$cmd $actual (>= $min_ver)"
    else
      err "$cmd $actual — version $min_ver or higher required"
      MISSING+=("$pkg")
      return 1
    fi
  else
    ok "$cmd — found"
  fi
}

check_dep "tmux"   "3.2" "tmux"  || true
check_dep "fish"   "3.4" "fish"  || true
check_dep "git"    ""    "git"   || true
check_dep "curl"   ""    "curl"  || true

# Python gets special handling — find 3.10+ anywhere on the system
PYTHON3=""
if PYTHON3=$(find_python3); then
  PY_VER="$($PYTHON3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')"
  ok "python3 $PY_VER ($PYTHON3)"
else
  err "python3 — version 3.10 or higher required (found only $(python3 --version 2>&1 || echo 'none'))"
  MISSING+=("python@3.12")
fi

# claude CLI is optional but recommended
if command -v claude &>/dev/null; then
  ok "claude — found"
else
  warn "claude CLI not found. Install it from https://claude.ai/code"
fi

# ── install missing deps ──────────────────────────────────────────────────────
if [[ ${#MISSING[@]} -gt 0 ]]; then
  hdr "Installing missing dependencies: ${MISSING[*]}"

  if [[ "$PKG_MGR" == "brew" ]] && ! command -v brew &>/dev/null; then
    info "Installing Homebrew…"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi

  for dep in "${MISSING[@]}"; do
    info "Installing $dep…"
    if pkg_install "$dep"; then
      ok "$dep installed"
    else
      err "Failed to install $dep — please install it manually and re-run."
    fi
  done

  # Re-detect python after installing
  if [[ -z "$PYTHON3" ]]; then
    if PYTHON3=$(find_python3); then
      PY_VER="$($PYTHON3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')"
      ok "python3 $PY_VER now available ($PYTHON3)"
    else
      die "Python 3.10+ still not found after install. Please install manually: brew install python@3.12"
    fi
  fi
fi

# ── install Python dependencies ───────────────────────────────────────────────
hdr "Installing Python dependencies…"

REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
if [[ -f "$REQUIREMENTS" ]]; then
  if "$PYTHON3" -m pip install -r "$REQUIREMENTS" --quiet; then
    ok "Python dependencies installed"
  else
    warn "pip install failed — trying with --user flag"
    if "$PYTHON3" -m pip install -r "$REQUIREMENTS" --user --quiet; then
      ok "Python dependencies installed (--user)"
    else
      err "Could not install Python dependencies. Run manually:"
      err "  $PYTHON3 -m pip install -r $REQUIREMENTS"
    fi
  fi
else
  warn "requirements.txt not found — skipping Python dependency install"
fi

# ── directory setup ───────────────────────────────────────────────────────────
hdr "Creating directories…"

CONFIG_DIR="${HOME}/.config/cc4u"
DATA_DIR="${HOME}/.local/share/cc4u"
BIN_USER="${HOME}/.local/bin"

for d in \
  "$CONFIG_DIR/widgets" \
  "$DATA_DIR/widgets" \
  "$DATA_DIR/themes" \
  "$DATA_DIR/layouts" \
  "$DATA_DIR/hooks" \
  "$BIN_USER" \
  "${HOME}/.claude"
do
  mkdir -p "$d"
done
ok "Directories created"

# ── install binary ────────────────────────────────────────────────────────────
hdr "Installing cc4u binary…"

BIN_SRC="$PROJECT_ROOT/bin/cc4u"
if [[ ! -f "$BIN_SRC" ]]; then
  die "Cannot find $BIN_SRC — run this script from the CC4U project root."
fi

# Prefer /usr/local/bin if writable, else ~/.local/bin
if [[ -d /usr/local/bin && -w /usr/local/bin ]]; then
  BIN_DEST="/usr/local/bin/cc4u"
else
  BIN_DEST="${BIN_USER}/cc4u"
fi

# Generate launcher with project root embedded
cat > "$BIN_DEST" <<LAUNCHER
#!/usr/bin/env bash
exec python3 "$PROJECT_ROOT/cc4u.py" "\$@"
LAUNCHER
chmod +x "$BIN_DEST"
ok "Installed binary → $BIN_DEST"

# ── install data files ────────────────────────────────────────────────────────
hdr "Copying CC4U data files…"

# Pricing data (needed by hooks for cost calculation)
if [[ -f "$PROJECT_ROOT/data/pricing.json" ]]; then
  cp "$PROJECT_ROOT/data/pricing.json" "$DATA_DIR/pricing.json"
  ok "Pricing data → $DATA_DIR/pricing.json"
fi

# Widgets
if [[ -d "$PROJECT_ROOT/lib/widgets" ]]; then
  cp -r "$PROJECT_ROOT/lib/widgets/." "$DATA_DIR/widgets/"
  ok "Widgets → $DATA_DIR/widgets/"
else
  warn "lib/widgets/ not found (skipped)"
fi

# Themes (in data/themes, not lib/themes)
if [[ -d "$PROJECT_ROOT/data/themes" ]]; then
  cp -r "$PROJECT_ROOT/data/themes/." "$DATA_DIR/themes/"
  ok "Themes → $DATA_DIR/themes/"
elif [[ -d "$PROJECT_ROOT/lib/themes" ]]; then
  cp -r "$PROJECT_ROOT/lib/themes/." "$DATA_DIR/themes/"
  ok "Themes → $DATA_DIR/themes/"
else
  warn "No themes directory found (skipped)"
fi

# Layouts (in data/layouts, not lib/layouts)
if [[ -d "$PROJECT_ROOT/data/layouts" ]]; then
  cp -r "$PROJECT_ROOT/data/layouts/." "$DATA_DIR/layouts/"
  ok "Layouts → $DATA_DIR/layouts/"
elif [[ -d "$PROJECT_ROOT/lib/layouts" ]]; then
  cp -r "$PROJECT_ROOT/lib/layouts/." "$DATA_DIR/layouts/"
  ok "Layouts → $DATA_DIR/layouts/"
else
  warn "No layouts directory found (skipped)"
fi

# Hooks
if [[ -d "$PROJECT_ROOT/hooks" ]]; then
  cp "$PROJECT_ROOT"/hooks/*.fish "$DATA_DIR/hooks/" 2>/dev/null || true
  chmod +x "$DATA_DIR"/hooks/*.fish 2>/dev/null || true
  ok "Hooks → $DATA_DIR/hooks/"
else
  warn "hooks/ not found (skipped)"
fi

# ── register hooks in ~/.claude/settings.json ─────────────────────────────────
hdr "Registering Claude Code hooks…"

CLAUDE_SETTINGS="${HOME}/.claude/settings.json"

if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
  echo '{}' > "$CLAUDE_SETTINGS"
fi

"$PYTHON3" - <<PYEOF
import json, os, sys
from pathlib import Path

settings_path = Path("$CLAUDE_SETTINGS")
hooks_dir = Path("$DATA_DIR/hooks")

try:
    settings = json.loads(settings_path.read_text())
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

hooks = settings.setdefault("hooks", {})

event_map = {
    "PostToolUse":  "post_tool_use.fish",
    "PreToolUse":   "pre_tool_use.fish",
    "Stop":         "stop.fish",
    "Notification": "notification.fish",
}

for event, fish_file in event_map.items():
    hook_path = hooks_dir / fish_file
    if not hook_path.exists():
        print(f"  ⚠ Hook not found: {hook_path}", file=sys.stderr)
        continue
    cmd = f"fish {hook_path}"
    event_hooks = hooks.setdefault(event, [])
    if cmd not in event_hooks:
        event_hooks.append(cmd)

settings_path.write_text(json.dumps(settings, indent=2))
print("Hooks registered in " + str(settings_path))
PYEOF

ok "Claude Code hooks registered"

# ── write default config ──────────────────────────────────────────────────────
hdr "Initialising config…"

CONFIG_FILE="$CONFIG_DIR/config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
  cat > "$CONFIG_FILE" <<'JSON'
{
  "theme": "dark",
  "layout": "default",
  "widgets": {
    "enabled": [],
    "order": []
  },
  "notifications": {
    "macos_native": true
  }
}
JSON
  ok "Default config written → $CONFIG_FILE"
else
  info "Config already exists → $CONFIG_FILE (unchanged)"
fi

# ── add CC4U init to fish config ──────────────────────────────────────────────
hdr "Configuring Fish shell…"

FISH_CONFIG="${HOME}/.config/fish/config.fish"
FISH_INIT_BLOCK="# CC4U init — added by install.sh"
FISH_INIT_LINE="set -gx PATH \$PATH ${BIN_USER}"

if [[ ! -f "$FISH_CONFIG" ]]; then
  mkdir -p "$(dirname "$FISH_CONFIG")"
  touch "$FISH_CONFIG"
fi

if grep -q "CC4U init" "$FISH_CONFIG"; then
  info "Fish config already contains CC4U init (skipped)"
else
  cat >> "$FISH_CONFIG" <<FISHEOF

$FISH_INIT_BLOCK
if not contains -- "$BIN_USER" \$PATH
    set -gx PATH \$PATH "$BIN_USER"
end
FISHEOF
  ok "CC4U PATH added to $FISH_CONFIG"
fi

# ── add to PATH for the current bash session ──────────────────────────────────
export PATH="$PATH:$BIN_USER"

# Also add to ~/.bashrc / ~/.zshrc if present
for RC_FILE in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
  if [[ -f "$RC_FILE" ]] && ! grep -q "CC4U" "$RC_FILE"; then
    echo "" >> "$RC_FILE"
    echo "# CC4U" >> "$RC_FILE"
    echo "export PATH=\"\$PATH:$BIN_USER\"" >> "$RC_FILE"
  fi
done

# ── verify installation ───────────────────────────────────────────────────────
hdr "Verifying installation…"

VERIFY_FAIL=0

if [[ -x "$BIN_DEST" ]]; then
  ok "cc4u binary is executable"
else
  err "cc4u binary missing or not executable at $BIN_DEST"
  VERIFY_FAIL=1
fi

if "$PYTHON3" "$BIN_DEST" version &>/dev/null; then
  CC4U_VER=$("$PYTHON3" "$BIN_DEST" version 2>/dev/null || echo "unknown")
  ok "cc4u $CC4U_VER responds correctly"
else
  warn "cc4u version check skipped (run 'cc4u version' to verify)"
fi

if [[ -f "$CONFIG_FILE" ]]; then
  ok "Config file present"
else
  err "Config file missing"
  VERIFY_FAIL=1
fi

if grep -q "PostToolUse" "${HOME}/.claude/settings.json" 2>/dev/null; then
  ok "Claude hooks registered"
else
  err "Claude hooks not found in settings.json"
  VERIFY_FAIL=1
fi

# ── final message ─────────────────────────────────────────────────────────────
echo
if [[ $VERIFY_FAIL -eq 0 ]]; then
  echo -e "${C_GRN}${C_BLD}CC4U installed successfully!${C_RST}"
else
  echo -e "${C_YEL}${C_BLD}CC4U installed with warnings — check errors above.${C_RST}"
fi

echo
echo "  Run  ${C_BLD}cc4u${C_RST}  to launch. The setup wizard will open on first run."
echo
echo "  To reset and re-run the wizard:  ${C_BLD}rm ~/.config/cc4u/config.json && cc4u${C_RST}"
echo

exit $VERIFY_FAIL
