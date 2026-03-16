#!/usr/bin/env bash
# Install a skill from the skills hub
#
# Usage: ./install_skill.sh <slug> [options]
#
# Options:
#   --version <version>  Install specific version
#   --no-enable          Do not enable after installation
#   --force              Overwrite existing skill

set -e

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

if [ -z "$1" ]; then
    echo "Error: Skill slug is required"
    echo "Usage: ./install_skill.sh <slug> [options]"
    exit 1
fi

SLUG="$1"
shift

# Forward all remaining arguments to the CLI
$COPAW_CMD skills install "$SLUG" "$@"
