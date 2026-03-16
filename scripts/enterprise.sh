#!/usr/bin/env bash
# Quick enterprise mode starter
# Usage: bash scripts/enterprise.sh [skill-url]

SKILL_URL="${1:-}"

bash /Users/wangyun/Documents/work/github/CoPaw/scripts/start_enterprise.sh \
    ${SKILL_URL:+--sync "$SKILL_URL"}
