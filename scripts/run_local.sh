#!/usr/bin/env bash
# CoPaw Local Testing Quick Start Script
# Usage: bash scripts/run_local.sh [OPTIONS] [--] [copaw_options]
#
# Quickly set up and run CoPaw from the current directory for local testing.
# Creates an isolated virtual environment (.venv_local) and installs CoPaw
# in editable mode. On macOS, mlx-lm is enabled by default.
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_ENV="$REPO_DIR/.venv_local"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
EXTRAS=""
REINIT=false
NO_MLX=false
BACKEND=""  # mlx, llamacpp, or empty (auto-detect)

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    RED="\033[0;31m"
    BLUE="\033[0;34m"
    RESET="\033[0m"
else
    BOLD="" GREEN="" YELLOW="" RED="" BLUE="" RESET=""
fi

info()  { printf "${GREEN}[copaw-local]${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}[copaw-local]${RESET} %s\n" "$*"; }
error() { printf "${RED}[copaw-local]${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# ── Show help ──────────────────────────────────────────────────────────────────
show_help() {
    cat <<EOF
${BOLD}CoPaw Local Testing Quick Start${RESET}

Usage: bash scripts/run_local.sh [OPTIONS] [--] [copaw_options]

${BOLD}Options:${RESET}
  --backend BACKEND    Local model backend: mlx, llamacpp, or none
                       (default: auto-detect macOS for mlx)
  --no-mlx             Disable mlx-lm (equivalent to --backend none)
  --reinit             Reinitialize environment (delete existing .venv_local)
  --python VER         Specify Python version (default: 3.12)
  -h, --help           Show this help

${BOLD}copaw_options:${RESET} Arguments passed to 'copaw app' (e.g., --port 9000)

${BOLD}Environment Variables:${RESET}
  PYTHON_VERSION  Override Python version (default: 3.12)

${BOLD}Notes:${RESET}
  - First run automatically calls 'copaw init --defaults --accept-security'
  - The virtual environment is stored at .venv_local/ in the repository
  - Console frontend is built automatically if not present
  - Use --backend mlx on macOS for Apple Silicon MLX support
  - Use --backend llamacpp for llama.cpp support (cross-platform)

${BOLD}Examples:${RESET}
  bash scripts/run_local.sh                      # Start with defaults (mlx on macOS)
  bash scripts/run_local.sh --backend mlx        # Force MLX backend
  bash scripts/run_local.sh --backend llamacpp   # Use llama.cpp backend
  bash scripts/run_local.sh -- --port 9000       # Custom port
  bash scripts/run_local.sh --no-mlx             # Disable MLX (legacy)
  PYTHON_VERSION=3.11 bash scripts/run_local.sh  # Use Python 3.11

EOF
}

# ── Parse arguments ────────────────────────────────────────────────────────────
COPAW_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend)
            BACKEND="$2"
            shift 2 ;;
        --no-mlx)
            NO_MLX=true
            shift ;;
        --reinit)
            REINIT=true
            shift ;;
        --python)
            PYTHON_VERSION="$2"
            shift 2 ;;
        -h|--help)
            show_help
            exit 0 ;;
        --)
            shift
            COPAW_ARGS=("$@")
            break ;;
        -*)
            die "Unknown option: $1 (try --help)" ;;
        *)
            COPAW_ARGS=("$@")
            break ;;
    esac
done

# ── OS detection ───────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Linux|Darwin) ;;
    *) die "Unsupported OS: $OS. This script supports Linux and macOS only." ;;
esac

# Determine extras based on OS, backend option, and user preference
if [[ -n "$BACKEND" ]]; then
    # User explicitly specified a backend
    case "$BACKEND" in
        mlx)
            if [[ "$OS" != "Darwin" ]]; then
                warn "MLX backend is only supported on macOS. Proceeding anyway..."
            fi
            EXTRAS="[mlx]"
            info "MLX backend requested via --backend mlx"
            ;;
        llamacpp)
            EXTRAS="[llamacpp]"
            info "llama.cpp backend requested via --backend llamacpp"
            ;;
        none)
            # No local backend extras
            info "No local backend requested via --backend none"
            ;;
        *)
            die "Unknown backend: $BACKEND (valid: mlx, llamacpp, none)"
            ;;
    esac
elif [[ "$NO_MLX" == "true" ]]; then
    # Legacy --no-mlx option
    info "MLX disabled via --no-mlx"
else
    # Auto-detect: enable MLX on macOS by default
    if [[ "$OS" == "Darwin" ]]; then
        EXTRAS="[mlx]"
        info "Detected macOS - will install with mlx-lm support (use --backend none to disable)"
    fi
fi

# Install modelscope if using MLX backend (for faster downloads in China)
if [[ "$EXTRAS" == "[mlx]" ]]; then
    info "Tip: Use '--source modelscope' when downloading models for faster speeds in China"
fi

# ── Step 1: Ensure uv is available ─────────────────────────────────────────────
ensure_uv() {
    if command -v uv &>/dev/null; then
        info "uv found: $(command -v uv)"
        return
    fi

    # Check common install locations not yet on PATH
    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            export PATH="$(dirname "$candidate"):$PATH"
            info "uv found: $candidate"
            return
        fi
    done

    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source the env file uv's installer creates, or add common paths
    if [ -f "$HOME/.local/bin/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.local/bin/env"
    fi
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    command -v uv &>/dev/null || die "Failed to install uv. Please install it manually: https://docs.astral.sh/uv/"
    info "uv installed successfully"
}

# ── Step 2: Prepare console frontend ───────────────────────────────────────────
prepare_console() {
    local console_src="$REPO_DIR/console/dist"
    local console_dest="$REPO_DIR/src/copaw/console"

    # Already populated
    if [ -f "$console_dest/index.html" ]; then
        return 0
    fi

    # Copy pre-built assets if available
    if [ -d "$console_src" ] && [ -f "$console_src/index.html" ]; then
        info "Copying console frontend assets..."
        mkdir -p "$console_dest"
        cp -R "$console_src/"* "$console_dest/"
        return 0
    fi

    # Try to build if npm is available
    if [ ! -f "$REPO_DIR/console/package.json" ]; then
        warn "Console source not found — the web UI won't be available."
        return 0
    fi

    if ! command -v npm &>/dev/null; then
        warn "npm not found — skipping console frontend build."
        warn "Install Node.js from https://nodejs.org/ or run 'cd console && npm ci && npm run build' manually."
        return 0
    fi

    info "Building console frontend (npm ci && npm run build)..."
    if (cd "$REPO_DIR/console" && npm ci && npm run build); then
        if [ -f "$console_src/index.html" ]; then
            mkdir -p "$console_dest"
            cp -R "$console_src/"* "$console_dest/"
            info "Console frontend built successfully"
        fi
    else
        warn "Console build failed — the web UI won't be available."
    fi
}

# ── Step 3: Create/update virtual environment ──────────────────────────────────
setup_venv() {
    # Handle reinit flag
    if [ "$REINIT" = true ] && [ -d "$LOCAL_ENV" ]; then
        info "Removing existing environment (--reinit)..."
        rm -rf "$LOCAL_ENV"
    fi

    if [ -d "$LOCAL_ENV" ]; then
        info "Existing environment found, upgrading..."
    else
        info "Creating Python $PYTHON_VERSION environment at .venv_local/..."
        uv venv "$LOCAL_ENV" --python "$PYTHON_VERSION"
    fi

    # Verify the venv was created
    [ -x "$LOCAL_ENV/bin/python" ] || die "Failed to create virtual environment"
    info "Python environment ready ($("$LOCAL_ENV/bin/python" --version))"

    # Install CoPaw from current directory
    info "Installing CoPaw from current directory${EXTRAS}..."
    if uv pip install -e "$REPO_DIR$EXTRAS" --python "$LOCAL_ENV/bin/python" --prerelease=allow; then
        info "CoPaw installed successfully"
    else
        die "Installation failed"
    fi

    # Verify the CLI entry point exists
    [ -x "$LOCAL_ENV/bin/copaw" ] || die "Installation failed: copaw CLI not found in venv"

    # Install modelscope for MLX backend (for ModelScope downloads)
    if [[ "$EXTRAS" == "[mlx]" ]]; then
        info "Installing modelscope for MLX ModelScope downloads..."
        if uv pip install modelscope --python "$LOCAL_ENV/bin/python" --quiet; then
            info "modelscope installed successfully"
        else
            warn "modelscope installation failed - ModelScope downloads may not work"
        fi
    fi
}

# ── Step 4: First-time initialization ───────────────────────────────────────────
maybe_init() {
    # Check if config exists in the default location
    if [ ! -f "$HOME/.copaw/config.json" ] && [ ! -f "$HOME/.copaw/working/config.json" ]; then
        info "First run detected - initializing with defaults..."
        # Need both --defaults and --accept-security for non-interactive mode
        "$LOCAL_ENV/bin/copaw" init --defaults --accept-security || warn "Initialization failed, but continuing..."
    fi
}

# ── Main execution ─────────────────────────────────────────────────────────────
main() {
    echo ""
    printf "${BLUE}${BOLD}CoPaw Local Testing Environment${RESET}\n"
    echo "========================================"
    echo ""

    ensure_uv
    prepare_console
    setup_venv
    maybe_init

    echo ""
    printf "${GREEN}${BOLD}Ready to start CoPaw!${RESET}\n"
    echo ""

    # Launch copaw app with any additional arguments
    if [ ${#COPAW_ARGS[@]} -gt 0 ]; then
        info "Starting: copaw app ${COPAW_ARGS[*]}"
        echo ""
        exec "$LOCAL_ENV/bin/copaw" app "${COPAW_ARGS[@]}"
    else
        info "Starting: copaw app"
        echo ""
        exec "$LOCAL_ENV/bin/copaw" app
    fi
}

main
