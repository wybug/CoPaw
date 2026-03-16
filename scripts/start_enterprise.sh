#!/usr/bin/env bash
# CoPaw Enterprise Mode Startup Script
# Usage: bash scripts/start_enterprise.sh [OPTIONS]
#
# Starts CoPaw with Enterprise Skills Hub for signed skill management.
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_ENV="$REPO_DIR/.venv"
HUB_DIR="$REPO_DIR/hub_enterprise"

# Default ports
HUB_PORT="${HUB_PORT:-9090}"
COPAW_PORT="${COPAW_PORT:-8089}"
COPAW_HOST="${COPAW_HOST:-127.0.0.1}"

# Paths
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-/tmp/test_keys/public_key.pem}"
PRIVATE_KEY_FILE="${PRIVATE_KEY_FILE:-/tmp/test_keys/private_key.pem}"
DATA_DIR="${DATA_DIR:-$HUB_DIR/hub_enterprise/skills_data}"

# Options
START_HUB="${START_HUB:-true}"
START_COPAW="${START_COPAW:-true}"
AUTO_SYNC="${AUTO_SYNC:-false}"
VERBOSE="${VERBOSE:-false}"

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

info()  { printf "${GREEN}[enterprise]${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}[enterprise]${RESET} %s\n" "$*"; }
error() { printf "${RED}[enterprise]${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# ── Show help ──────────────────────────────────────────────────────────────────
show_help() {
    cat <<EOF
${BOLD}CoPaw Enterprise Mode Startup${RESET}

Usage: bash scripts/start_enterprise.sh [OPTIONS]

${BOLD}Options:${RESET}
  --no-hub             Don't start Enterprise Hub
  --no-copaw           Don't start CoPaw app
  --hub-port PORT      Enterprise Hub port (default: 9090)
  --copaw-port PORT    CoPaw app port (default: 8089)
  --public-key FILE    Path to public key file
  --private-key FILE   Path to private key file
  --data-dir DIR       Hub data directory
  --sync SKILL         Auto-sync a skill from URL
  -v, --verbose        Show verbose output
  -h, --help           Show this help

${BOLD}Environment Variables:${RESET}
  HUB_PORT             Enterprise Hub port (default: 9090)
  COPAW_PORT           CoPaw app port (default: 8089)
  COPAW_HOST           CoPaw app host (default: 127.0.0.1)
  PUBLIC_KEY_FILE      Public key file for verification
  PRIVATE_KEY_FILE     Private key file for signing
  DATA_DIR             Hub data directory

${BOLD}Examples:${RESET}
  bash scripts/start_enterprise.sh                    # Start all services
  bash scripts/start_enterprise.sh --hub-port 9000  # Custom Hub port
  bash scripts/start_enterprise.sh --no-copaw       # Start Hub only
  bash scripts/start_enterprise.sh --sync "https://github.com/owner/skill"

${BOLD}Notes:${RESET}
  - Enterprise Hub runs on http://localhost:\${HUB_PORT}
  - CoPaw Console runs on http://\${COPAW_HOST}:\${COPAW_PORT}
  - RSA signatures are used for skill verification
  - Generate keys with: .venv/bin/skills-sync generate-key-pair

EOF
}

# ── Parse arguments ────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-hub)
            START_HUB=false
            shift ;;
        --no-copaw)
            START_COPAW=false
            shift ;;
        --hub-port)
            HUB_PORT="$2"
            shift 2 ;;
        --copaw-port)
            COPAW_PORT="$2"
            shift 2 ;;
        --public-key)
            PUBLIC_KEY_FILE="$2"
            shift 2 ;;
        --private-key)
            PRIVATE_KEY_FILE="$2"
            shift 2 ;;
        --data-dir)
            DATA_DIR="$2"
            shift 2 ;;
        --sync)
            AUTO_SYNC="$2"
            shift 2 ;;
        -v|--verbose)
            VERBOSE=true
            shift ;;
        -h|--help)
            show_help
            exit 0 ;;
        *)
            die "Unknown option: $1 (try --help)"
            ;;
    esac
done

# ── Helper functions ───────────────────────────────────────────────────────────
check_port() {
    local port="$1"
    local name="$2"
    if lsof -i ":$port" &>/dev/null; then
        warn "Port $port already in use - $name may not start properly"
    fi
}

wait_for_service() {
    local url="$1"
    local name="$2"
    local max_wait="${3:-30}"
    local count=0

    while [ $count -lt $max_wait ]; do
        if curl -s "$url" &>/dev/null; then
            info "$name is ready"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    warn "$name did not respond within ${max_wait}s"
    return 1
}

# ── Step 1: Generate keys if needed ─────────────────────────────────────────────
ensure_keys() {
    if [ ! -f "$PUBLIC_KEY_FILE" ] || [ ! -f "$PRIVATE_KEY_FILE" ]; then
        info "Generating RSA key pair..."
        mkdir -p "$(dirname "$PUBLIC_KEY_FILE")"
        mkdir -p "$(dirname "$PRIVATE_KEY_FILE")"

        "$LOCAL_ENV/bin/python" -c "
from hub_enterprise.signature import generate_key_pair
private, public = generate_key_pair()
with open('$PRIVATE_KEY_FILE', 'w') as f:
    f.write(private)
with open('$PUBLIC_KEY_FILE', 'w') as f:
    f.write(public)
"
        chmod 600 "$PRIVATE_KEY_FILE"
        info "Keys generated: $PUBLIC_KEY_FILE, $PRIVATE_KEY_FILE"
    else
        info "Using existing keys: $PUBLIC_KEY_FILE"
    fi
}

# ── Step 2: Start Enterprise Hub ───────────────────────────────────────────────
start_hub() {
    check_port "$HUB_PORT" "Enterprise Hub"

    info "Starting Enterprise Skills Hub on port $HUB_PORT..."

    cd "$HUB_DIR"

    # Set Hub environment variables
    export HUB_HOST="0.0.0.0"
    export HUB_PORT="$HUB_PORT"
    export HUB_PRIVATE_KEY="$(cat "$PRIVATE_KEY_FILE" 2>/dev/null || echo "")"
    export HUB_DATA_DIR="$DATA_DIR"

    if [ "$VERBOSE" = "true" ]; then
        "$LOCAL_ENV/bin/python" -m hub_enterprise &
    else
        "$LOCAL_ENV/bin/python" -m hub_enterprise > /tmp/hub_enterprise.log 2>&1 &
    fi

    HUB_PID=$!
    echo "$HUB_PID" > /tmp/hub_enterprise.pid

    info "Enterprise Hub started (PID: $HUB_PID)"
    info "API: http://localhost:$HUB_PORT"
    info "Docs: http://localhost:$HUB_PORT/docs"

    # Wait for Hub to be ready
    wait_for_service "http://localhost:$HUB_PORT/health" "Enterprise Hub"
}

# ── Step 3: Start CoPaw with enterprise config ─────────────────────────────
start_copaw() {
    check_port "$COPAW_PORT" "CoPaw"

    info "Starting CoPaw with enterprise mode configuration..."

    # Set enterprise environment variables
    export COPAW_SKILLS_HUB_BASE_URL="http://localhost:$HUB_PORT"
    export COPAW_SKILLS_HUB_PUBLIC_KEY="$(cat "$PUBLIC_KEY_FILE")"
    export COPAW_EMPLOYEE_ID="${COPAW_EMPLOYEE_ID:-enterprise-user}"

    cd "$REPO_DIR"

    if [ "$VERBOSE" = "true" ]; then
        "$LOCAL_ENV/bin/copaw" app --host "$COPAW_HOST" --port "$COPAW_PORT" &
    else
        "$LOCAL_ENV/bin/copaw" app --host "$COPAW_HOST" --port "$COPAW_PORT" > /tmp/copaw_enterprise.log 2>&1 &
    fi

    COPAW_PID=$!
    echo "$COPAW_PID" > /tmp/copaw_enterprise.pid

    info "CoPaw started (PID: $COPAW_PID)"
    info "Console: http://$COPAW_HOST:$COPAW_PORT"

    # Wait for CoPaw to be ready
    sleep 3
}

# ── Step 4: Auto-sync skill if requested ───────────────────────────────────────
sync_skill() {
    local skill_url="$1"
    if [ -z "$skill_url" ]; then
        return
    fi

    info "Auto-syncing skill: $skill_url"
    sleep 2  # Wait for Hub to be fully ready

    "$LOCAL_ENV/bin/skills-sync" sync auto "$skill_url" \
        --auto-approve \
        --private-key-file "$PRIVATE_KEY_FILE" \
        --direct \
        --data-dir "$DATA_DIR"
}

# ── Main execution ─────────────────────────────────────────────────────────────
main() {
    echo ""
    printf "${CYAN}${BOLD}CoPaw Enterprise Mode${RESET}\n"
    echo "========================================"
    echo ""

    # Verify environment
    if [ ! -d "$LOCAL_ENV" ]; then
        die "Virtual environment not found. Run 'bash scripts/run_local.sh' first."
    fi

    if [ ! -f "$LOCAL_ENV/bin/skills-sync" ]; then
        die "skills-sync not found. Ensure hub-enterprise is installed."
    fi

    # Ensure keys exist
    ensure_keys

    # Start services
    if [ "$START_HUB" = "true" ]; then
        start_hub
    fi

    if [ "$START_COPAW" = "true" ]; then
        start_copaw
    fi

    # Auto-sync skill if requested
    if [ -n "$AUTO_SYNC" ]; then
        sync_skill "$AUTO_SYNC"
    fi

    echo ""
    printf "${GREEN}${BOLD}Enterprise Mode Ready!${RESET}\n"
    echo ""
    echo "Services:"
    if [ "$START_HUB" = "true" ]; then
        echo "  • Enterprise Hub:  http://localhost:$HUB_PORT"
        echo "    - API Docs:      http://localhost:$HUB_PORT/docs"
        echo "    - Health Check:  http://localhost:$HUB_PORT/health"
    fi
    if [ "$START_COPAW" = "true" ]; then
        echo "  • CoPaw Console:   http://$COPAW_HOST:$COPAW_PORT"
    fi
    echo ""
    echo "Configuration:"
    echo "  • Public Key:  $PUBLIC_KEY_FILE"
    echo "  • Private Key: $PRIVATE_KEY_FILE"
    echo "  • Data Dir:    $DATA_DIR"
    echo ""
    echo "Commands:"
    echo "  • Stop all:      pkill -f 'hub_enterprise|copaw app'"
    echo "  • Stop Hub:     kill \$(cat /tmp/hub_enterprise.pid)"
    echo "  • Stop CoPaw:   kill \$(cat /tmp/copaw_enterprise.pid)"
    echo "  • Sync skill:    .venv/bin/skills-sync sync auto <url> --auto-approve \\"
    echo "                    --private-key-file $PRIVATE_KEY_FILE --direct --data-dir $DATA_DIR"
    echo ""
    printf "${BLUE}${BOLD}Press Ctrl+C to stop all services${RESET}\n"
    echo ""

    # Wait for interrupt
    trap 'echo ""; info "Shutting down..."; pkill -f "hub_enterprise"; pkill -f "copaw app --host $COPAW_HOST --port $COPAW_PORT"; exit 0' INT TERM

    # Keep script running
    wait
}

main
