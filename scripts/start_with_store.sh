#!/bin/bash
# -*- coding: utf-8 -*-
"""Start Enterprise Hub and CoPaw together with pre-populated skills and MCP servers."""

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# Kill existing processes
echo -e "${BLUE}Stopping existing services...${NC}"
pkill -f "hub_enterprise" 2>/dev/null || true
pkill -f "copaw app" 2>/dev/null || true
sleep 2

# Start Enterprise Hub
echo -e "${BLUE}Starting Enterprise Hub...${NC}"
source .venv/bin/activate
cd hub_enterprise
python -m hub_enterprise > /tmp/hub_enterprise.log 2>&1 &
HUB_PID=$!
echo "Hub PID: $HUB_PID"

# Wait for Hub to be ready
echo "Waiting for Hub to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:9090/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Enterprise Hub ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}✗ Hub failed to start${NC}"
        cat /tmp/hub_enterprise.log
        exit 1
    fi
    sleep 1
done

# Start CoPaw with local Hub configuration
echo -e "${BLUE}Starting CoPaw with local Hub...${NC}"
cd "$REPO_DIR"
export COPAW_SKILLS_HUB_BASE_URL="http://127.0.0.1:9090"
export COPAW_MCP_HUB_BASE_URL="http://127.0.0.1:9090"
copaw app > /tmp/copaw_with_hub.log 2>&1 &
COPAW_PID=$!
echo "CoPaw PID: $COPAW_PID"

# Wait for CoPaw to be ready
echo "Waiting for CoPaw to start..."
sleep 4

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Enterprise Store Ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services:"
echo -e "  • Enterprise Hub:  ${BLUE}http://127.0.0.1:9090${NC}"
echo -e "    - API Docs:      ${BLUE}http://127.0.0.1:9090/docs${NC}"
echo "  • CoPaw Console:   ${BLUE}http://127.0.0.1:8088${NC}"
echo -e "    - Enterprise Store: ${BLUE}http://127.0.0.1:8088/enterprise-store${NC}"
echo ""
echo "Pre-populated Resources:"
echo "  • Skills Store: 1+ skills (including Weather Query)"
echo "  • MCP Store: 8 servers (tavily-search, fetch, etc.)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Stopping services...${NC}"
    kill $HUB_PID 2>/dev/null || true
    kill $COPAW_PID 2>/dev/null || true
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

# Keep script running
wait
