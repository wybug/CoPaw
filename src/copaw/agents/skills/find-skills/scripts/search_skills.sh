#!/usr/bin/env bash
# Search for skills from the skills hub
#
# Usage: ./search_skills.sh [query] [limit]

set -e

QUERY="${1:-}"
LIMIT="${2:-20}"

# Find copaw command - try PATH first, then use Python module
if command -v copaw &> /dev/null; then
    COPAW_CMD="copaw"
else
    # Find Python executable
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python not found in PATH"
        exit 1
    fi
    # Use Python module as fallback
    COPAW_CMD="$PYTHON_CMD -m copaw"
fi

# Call the CoPaw CLI search command
$COPAW_CMD skills search "$QUERY" --limit "$LIMIT"
