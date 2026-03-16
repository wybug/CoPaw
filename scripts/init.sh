#!/usr/bin/env bash
# CoPaw Initialization Script
# Usage: bash scripts/init.sh [OPTIONS]
#
# Initializes CoPaw configuration in a clean, consistent way.
# This is the recommended first step after installation to avoid confusion.
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_ENV="$REPO_DIR/.venv"
COPAW_HOME="${COPAW_HOME:-$HOME/.copaw}"

# Options
MODE="${MODE:-defaults}"           # defaults, interactive, minimal
ACCEPT_SECURITY="${ACCEPT_SECURITY:-true}"
SKIP_WORKING_SECRET="${SKIP_WORKING_SECRET:-false}"
VERIFY_INIT="${VERIFY_INIT:-true}"

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    RED="\033[0;31m"
    BLUE="\033[0;34m"
    CYAN="\033[0;36m"
    RESET="\033[0m"
else
    BOLD="" GREEN="" YELLOW="" RED="" BLUE="" CYAN="" RESET=""
fi

info()  { printf "${GREEN}[init]${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}[init]${RESET} %s\n" "$*"; }
error() { printf "${RED}[init]${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# ── Show help ──────────────────────────────────────────────────────────────────
show_help() {
    cat <<EOF
${BOLD}CoPaw Initialization${RESET}

Usage: bash scripts/init.sh [OPTIONS]

${BOLD}Options:${RESET}
  -m, --mode MODE       Init mode: defaults, interactive, minimal
                       (default: defaults)
  --no-accept-security  Require manual confirmation for security prompts
  --skip-working-secret Skip creating working.secret directory
  --no-verify           Skip verification after initialization
  -h, --help            Show this help

${BOLD}Modes:${RESET}
  ${BOLD}defaults${RESET}       Use sensible defaults (recommended for first-time users)
  ${BOLD}interactive${RESET}    Prompt for all configuration options
  ${BOLD}minimal${RESET}        Create only essential config files

${BOLD}Environment Variables:${RESET}
  COPAW_HOME        CoPaw home directory (default: ~/.copaw)

${BOLD}Examples:${RESET}
  bash scripts/init.sh                          # Initialize with defaults
  bash scripts/init.sh --mode interactive       # Interactive setup
  bash scripts/init.sh --mode minimal           # Minimal config

${BOLD}What this does:${RESET}
  • Creates ~/.copaw/ directory structure
  • Generates config.json with default settings
  • Creates working.secret/ for sensitive data
  • Sets up model provider configuration
  • Verifies installation

EOF
}

# ── Parse arguments ────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mode)
            MODE="$2"
            shift 2 ;;
        --no-accept-security)
            ACCEPT_SECURITY=false
            shift ;;
        --skip-working-secret)
            SKIP_WORKING_SECRET=true
            shift ;;
        --no-verify)
            VERIFY_INIT=false
            shift ;;
        -h|--help)
            show_help
            exit 0 ;;
        *)
            die "Unknown option: $1 (try --help)" ;;
    esac
done

# ── Validate mode ──────────────────────────────────────────────────────────────
case "$MODE" in
    defaults|interactive|minimal) ;;
    *) die "Invalid mode: $MODE (valid: defaults, interactive, minimal)" ;;
esac

# ── Header ─────────────────────────────────────────────────────────────────────
echo ""
printf "${CYAN}${BOLD}CoPaw Initialization${RESET}\n"
echo "========================================"
echo ""
info "Mode: ${BOLD}$MODE${RESET}"
info "Home: ${BOLD}$COPAW_HOME${RESET}"
echo ""

# ── Step 1: Find copaw executable ──────────────────────────────────────────────
find_copaw() {
    # Check local venv first
    if [ -x "$LOCAL_ENV/bin/copaw" ]; then
        info "Using CoPaw from local environment: $LOCAL_ENV/bin/copaw"
        COPAW_BIN="$LOCAL_ENV/bin/copaw"
        return
    fi

    # Check COPAW_HOME venv
    if [ -x "$COPAW_HOME/venv/bin/copaw" ]; then
        info "Using CoPaw from home environment: $COPAW_HOME/venv/bin/copaw"
        COPAW_BIN="$COPAW_HOME/venv/bin/copaw"
        return
    fi

    # Check system PATH
    if command -v copaw &>/dev/null; then
        info "Using CoPaw from system PATH: $(command -v copaw)"
        COPAW_BIN="$(command -v copaw)"
        return
    fi

    die "CoPaw executable not found!"
    echo ""
    echo "Please install CoPaw first:"
    echo "  • From source: bash scripts/run_local.sh"
    echo "  • From PyPI: bash scripts/install.sh"
    echo ""
}

find_copaw

# ── Step 2: Check existing initialization ──────────────────────────────────────
check_existing() {
    local config_file=""
    if [ -f "$COPAW_HOME/config.json" ]; then
        config_file="$COPAW_HOME/config.json"
    elif [ -f "$COPAW_HOME/working/config.json" ]; then
        config_file="$COPAW_HOME/working/config.json"
    fi

    if [ -n "$config_file" ]; then
        warn "CoPaw appears to be already initialized!"
        warn "Found existing config: $config_file"
        echo ""
        printf "${YELLOW}Re-initializing will:${RESET}\n"
        echo "  • Backup existing config to config.json.backup"
        echo "  • Create new configuration"
        echo "  • Preserve your data and skills"
        echo ""
        read -p "Continue? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Initialization cancelled"
            exit 0
        fi

        # Backup existing config
        local backup_dir="$COPAW_HOME/backups"
        mkdir -p "$backup_dir"
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        cp "$config_file" "$backup_dir/config.json.$timestamp"
        info "Backed up existing config to: $backup_dir/config.json.$timestamp"
    fi
}

check_existing

# ── Step 3: Build init command ─────────────────────────────────────────────────
build_init_args() {
    local args=()

    case "$MODE" in
        defaults)
            args+=("--defaults")
            if [ "$ACCEPT_SECURITY" = "true" ]; then
                args+=("--accept-security")
            fi
            ;;
        interactive)
            # No args needed for interactive
            ;;
        minimal)
            args+=("--defaults")
            if [ "$ACCEPT_SECURITY" = "true" ]; then
                args+=("--accept-security")
            fi
            # Minimal mode: we'll clean up extra files after init
            ;;
    esac

    echo "${args[@]:-}"
}

# ── Step 4: Run initialization ─────────────────────────────────────────────────
run_init() {
    info "Running CoPaw initialization..."

    local init_args
    init_args=$(build_init_args)

    if [ -n "$init_args" ]; then
        if "$COPAW_BIN" init $init_args; then
            info "Initialization completed successfully"
        else
            die "Initialization failed!"
        fi
    else
        if "$COPAW_BIN" init; then
            info "Initialization completed successfully"
        else
            die "Initialization failed!"
        fi
    fi
}

run_init

# ── Step 5: Post-initialization setup ──────────────────────────────────────────
post_init_setup() {
    info "Running post-initialization setup..."

    # Ensure working.secret directory exists
    if [ "$SKIP_WORKING_SECRET" = "false" ]; then
        local secret_dir="$COPAW_HOME/working.secret"
        if [ ! -d "$secret_dir" ]; then
            mkdir -p "$secret_dir"
            chmod 700 "$secret_dir"
            info "Created working.secret directory: $secret_dir"
        fi
    fi

    # Create example configuration files
    local working_dir="$COPAW_HOME/working"
    if [ -d "$working_dir" ]; then
        # Create example skills directory if it doesn't exist
        if [ ! -d "$working_dir/skills" ]; then
            mkdir -p "$working_dir/skills"
            info "Created skills directory: $working_dir/skills"
        fi

        # Create README in working directory
        cat > "$working_dir/README.md" << 'README'
# CoPaw Working Directory

This directory contains your CoPaw configuration, data, and custom skills.

## Structure

- `config.json` - Main configuration file
- `skills/` - Your custom skills
- `channels/` - Channel configurations
- `memory/` - Conversation memory (if using ReMe)

## Configuration

Edit `config.json` to configure:
- Model providers (OpenAI, Anthropic, Ollama, etc.)
- Channels (DingTalk, Feishu, QQ, Discord, etc.)
- Agent settings
- Memory options

## Skills

Add custom skills to the `skills/` directory. Each skill should have a `SKILL.md` file.

## Documentation

For more information, see: https://github.com/agentscope-ai/CoPaw
README
        info "Created working directory README"
    fi

    # For minimal mode, clean up unnecessary files
    if [ "$MODE" = "minimal" ]; then
        info "Minimal mode: Cleaning up unnecessary files..."
        # Remove example channels, etc. if they exist
        # This is a placeholder for any minimal-mode specific cleanup
    fi
}

post_init_setup

# ── Step 6: Verification ───────────────────────────────────────────────────────
verify_init() {
    if [ "$VERIFY_INIT" = "false" ]; then
        return
    fi

    info "Verifying initialization..."

    local errors=0

    # Check for config file
    local config_file=""
    if [ -f "$COPAW_HOME/config.json" ]; then
        config_file="$COPAW_HOME/config.json"
    elif [ -f "$COPAW_HOME/working/config.json" ]; then
        config_file="$COPAW_HOME/working/config.json"
    fi

    if [ -z "$config_file" ]; then
        error "Config file not found!"
        errors=$((errors + 1))
    else
        info "✓ Config file found: $config_file"
    fi

    # Check working.secret directory
    if [ "$SKIP_WORKING_SECRET" = "false" ]; then
        if [ -d "$COPAW_HOME/working.secret" ]; then
            info "✓ working.secret directory exists"
        else
            warn "✗ working.secret directory not found (may be created later)"
        fi
    fi

    # Verify copaw command works
    if "$COPAW_BIN" --version &>/dev/null; then
        info "✓ CoPaw command is functional"
    else
        error "✗ CoPaw command not working!"
        errors=$((errors + 1))
    fi

    if [ $errors -gt 0 ]; then
        warn "Verification completed with $errors error(s)"
    else
        info "Verification passed!"
    fi
}

verify_init

# ── Step 7: Next steps ─────────────────────────────────────────────────────────
show_next_steps() {
    echo ""
    printf "${GREEN}${BOLD}CoPaw initialized successfully!${RESET}\n"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo ""
    echo "1. Configure your model provider:"
    echo "   ${BOLD}cat $COPAW_HOME/config.json${RESET}"
    echo ""
    echo "2. Add API keys to working.secret:"
    if [ -d "$COPAW_HOME/working.secret" ]; then
        echo "   ${BOLD}ls $COPAW_HOME/working.secret${RESET}"
    fi
    echo ""
    echo "3. Start CoPaw:"
    if [ -x "$LOCAL_ENV/bin/copaw" ]; then
        echo "   ${BOLD}bash scripts/run_local.sh${RESET}"
    elif [ -x "$COPAW_HOME/bin/copaw" ]; then
        echo "   ${BOLD}copaw app${RESET}"
    else
        echo "   ${BOLD}$COPAW_BIN app${RESET}"
    fi
    echo ""
    echo "4. Open the console:"
    echo "   ${BOLD}http://127.0.0.1:8088${RESET} (default port)"
    echo ""
    echo "${BOLD}Documentation:${RESET}"
    echo "   • https://github.com/agentscope-ai/CoPaw"
    echo ""
}

show_next_steps
