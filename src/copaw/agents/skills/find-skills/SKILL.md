---
name: find-skills
description: "Guide users to discover and install skills from the skills hub. Search available skills and install skills using CoPaw CLI commands. Supports both standard mode (public ClawHub) and enterprise mode (private hub with signature verification and audit logging)."
metadata:
  copaw:
    emoji: "🔍"
---

# Find Skills from Hub

## Overview

The `find-skills` skill enables AI agents to help users discover and install skills from the CoPaw skills hub. It uses **CoPaw CLI commands** for all operations, providing a secure and consistent interface.

## Architecture

```
User → find-skills shell scripts → CoPaw CLI → Core logic
                                       ↓
                                  Security layer
                                  (keys, signatures, audit)
```

## Quick Start

### Search for Skills

```bash
# Using the shell script
~/.copaw/active_skills/find-skills/scripts/search_skills.sh "pdf" 10

# Or using CLI directly
copaw skills search "pdf" --limit 10
```

### Install a Skill

```bash
# Using the shell script
~/.copaw/active_skills/find-skills/scripts/install_skill.sh pdf --enable

# Or using CLI directly
copaw skills install pdf --enable
```

### List Installed Skills

```bash
copaw skills list
```

## Enterprise Mode

When enterprise mode is enabled (via `COPAW_SKILLS_HUB_PUBLIC_KEY`):

- **Signature Verification**: All installed skills are verified against the enterprise public key
- **Audit Logging**: All install actions are logged to the enterprise hub
- **Private Hub Only**: Access to public ClawHub is prohibited
- **Employee Tracking**: Actions are attributed to the employee ID (`COPAW_EMPLOYEE_ID`)

### Enterprise Environment Setup

```bash
export COPAW_SKILLS_HUB_BASE_URL="http://localhost:9090"
export COPAW_SKILLS_HUB_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."
export COPAW_EMPLOYEE_ID="user123"
```

### Enterprise Installation

In enterprise mode, you can install skills directly by slug:

```bash
# Enterprise mode - uses enterprise hub URL
copaw skills install my-skill --enable

# The CLI automatically:
# 1. Uses the enterprise hub URL
# 2. Verifies the skill signature
# 3. Logs the installation to the audit trail
```

## CLI Commands

### `copaw skills search`

Search for skills by keyword.

```bash
copaw skills search [query] --limit [number]
```

**Arguments:**
- `query` (optional): Search query string (default: empty, returns all skills)

**Options:**
- `--limit`: Maximum number of results (default: 20)

**Example:**
```bash
copaw skills search "automation" --limit 10
```

### `copaw skills install`

Install a skill from the hub (supports slug-based installation).

```bash
copaw skills install <slug> [options]
```

**Arguments:**
- `slug`: Skill slug to install (required)

**Options:**
- `--version`: Specific version to install (default: latest)
- `--no-enable`: Do not enable skill after installation
- `--force`: Overwrite if skill already exists

**Example:**
```bash
copaw skills install pdf --enable --force
```

### `copaw skills list`

Show all skills and their enabled/disabled status.

```bash
copaw skills list
```

## Shell Scripts

The find-skills skill provides wrapper shell scripts for convenience:

### `search_skills.sh`

Search for skills by keyword.

```bash
./search_skills.sh [query] [limit]
```

**Example:**
```bash
./search_skills.sh "pdf" 10
```

### `install_skill.sh`

Install a skill from the hub.

```bash
./install_skill.sh <slug> [options]
```

**Example:**
```bash
./install_skill.sh pdf --enable
```

## Error Handling

### Enterprise Mode Errors

If you see an error about enterprise mode:

```
ValueError: Enterprise mode is enabled. Access to public ClawHub is prohibited.
```

Set the correct hub URL:
```bash
export COPAW_SKILLS_HUB_BASE_URL="http://your-enterprise-hub:9090"
```

### Signature Verification Errors

If signature verification fails in enterprise mode:

```
ValueError: Enterprise Hub skill signature verification failed.
```

This means:
1. The skill was not signed by your enterprise
2. The skill may have been tampered with
3. The public key is incorrect

Contact your enterprise hub administrator.

### Connection Errors

If the hub is unreachable:

```
RuntimeError: Failed to request hub URL: https://clawhub.ai/api/v1/search
```

Check:
1. Network connectivity
2. Hub URL is correct
3. Hub is running and accessible

## AI Integration Patterns

### Finding Skills for a Task

When a user asks "I need to process PDF files", the AI should:

1. Search for relevant skills:
   ```bash
   copaw skills search "pdf" --limit 10
   ```

2. Present options to the user
3. If user chooses, install the skill:
   ```bash
   copaw skills install pdf --enable
   ```

### Browsing Available Skills

When a user asks "What skills are available?":

1. Search with empty query to get all skills:
   ```bash
   copaw skills search "" --limit 50
   ```

2. Present categorized results
3. Offer to install any selected skills

### Installing from a URL

When a user provides a hub URL directly:

1. Extract the slug from the URL (e.g., `pdf` from `https://clawhub.ai/skills/pdf`)
2. Use the install command with the slug:
   ```bash
   copaw skills install pdf --enable
   ```

## Enterprise Workflow

In enterprise mode, the typical workflow is:

1. **Admin configures environment**:
   - Sets hub URL (`COPAW_SKILLS_HUB_BASE_URL`)
   - Distributes public key (`COPAW_SKILLS_HUB_PUBLIC_KEY`)
   - Assigns employee IDs (`COPAW_EMPLOYEE_ID`)

2. **User searches for skills**:
   - Audit log is created automatically
   - Only enterprise-approved skills are shown

3. **User installs skill**:
   - Signature is verified automatically
   - Installation is logged to audit trail
   - Skill is enabled automatically

## Security Best Practices

1. **Never access secrets directly**: The shell scripts call CLI commands, which handle all security
2. **Enterprise mode enforcement**: The CLI enforces enterprise mode restrictions
3. **Signature verification**: Automatic in enterprise mode
4. **Audit logging**: Automatic for all enterprise operations

## Next Steps

For more usage examples and workflows, see `references/USAGE.md`.
