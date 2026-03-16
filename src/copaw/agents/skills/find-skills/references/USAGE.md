# Find Skills Usage Guide

This guide provides detailed usage examples and workflows for the `find-skills` skill.

## Table of Contents

- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Common Workflows](#common-workflows)
- [Enterprise Mode Workflows](#enterprise-mode-workflows)
- [AI Integration Examples](#ai-integration-examples)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic Search and Install

```bash
# Search for skills
copaw skills search "pdf" --limit 10

# Install a skill
copaw skills install pdf --enable

# List all skills
copaw skills list
```

### Using Shell Scripts

```bash
# Navigate to the skill directory
cd ~/.copaw/active_skills/find-skills/scripts

# Search for skills
./search_skills.sh "pdf" 10

# Install a skill
./install_skill.sh pdf --enable
```

## CLI Commands

### `copaw skills search`

Search for skills in the skills hub.

**Syntax:**
```bash
copaw skills search [query] --limit [number]
```

**Arguments:**
- `query` (optional): Search query string. Empty string returns all skills.

**Options:**
- `--limit`: Maximum number of results (default: 20)

**Examples:**
```bash
# Search for PDF-related skills
copaw skills search "pdf" --limit 10

# Get all available skills
copaw skills search "" --limit 50

# Search with default limit
copaw skills search "automation"
```

### `copaw skills install`

Install a skill from the hub using its slug.

**Syntax:**
```bash
copaw skills install <slug> [options]
```

**Arguments:**
- `slug`: Skill slug to install (required)

**Options:**
- `--version <version>`: Install a specific version (default: latest)
- `--no-enable`: Install but do not enable the skill
- `--force`: Overwrite if skill already exists

**Examples:**
```bash
# Install and enable
copaw skills install pdf --enable

# Install without enabling
copaw skills install pdf --no-enable

# Install specific version
copaw skills install pdf --version "1.2.3"

# Force reinstall
copaw skills install pdf --force
```

### `copaw skills list`

Show all installed skills and their status.

**Syntax:**
```bash
copaw skills list
```

**Example Output:**
```
──────────────────────────────────────────────────
  Skill Name                     Source       Status
──────────────────────────────────────────────────
  find-skills                    builtin      ✓ enabled
  pdf                            hub          ✓ enabled
  docx                           hub          ✗ disabled
──────────────────────────────────────────────────
  Total: 3 skills, 2 enabled, 1 disabled
```

## Common Workflows

### Workflow 1: Discover Skills for a Task

**Scenario**: User needs to process PDF files.

1. Search for PDF-related skills:
   ```bash
   copaw skills search "pdf" --limit 10
   ```

2. Review the results and pick a skill (e.g., `pdf`).

3. Install the skill:
   ```bash
   copaw skills install pdf --enable
   ```

4. Verify installation:
   ```bash
   copaw skills list
   ```

### Workflow 2: Browse All Available Skills

**Scenario**: User wants to explore what's available.

1. Search without a query to get all skills:
   ```bash
   copaw skills search "" --limit 50
   ```

2. Review categories and pick skills of interest.

3. Install desired skills:
   ```bash
   copaw skills install skill-name --enable
   ```

### Workflow 3: Install Specific Version

**Scenario**: User needs a specific version of a skill.

```bash
copaw skills install pdf --version "1.2.3" --enable
```

### Workflow 4: Update Existing Skill

**Scenario**: Update an already installed skill.

```bash
copaw skills install pdf --force
```

The `--force` flag overwrites the existing skill with the latest version.

### Workflow 5: Install Without Enabling

**Scenario**: Install a skill but don't enable it yet.

```bash
copaw skills install pdf --no-enable
```

Enable later:
```bash
copaw skills config
```

## Enterprise Mode Workflows

### Enterprise Setup Workflow

**For Administrators:**

1. Configure the enterprise hub:
   ```bash
   export COPAW_SKILLS_HUB_BASE_URL="http://enterprise-hub:9090"
   export COPAW_SKILLS_HUB_PUBLIC_KEY="$(cat /path/to/public_key.pem)"
   ```

2. Verify configuration:
   ```bash
   copaw skills search "test" --limit 1
   ```

3. Distribute employee ID to users:
   ```bash
   export COPAW_EMPLOYEE_ID="user123"
   ```

### Enterprise User Workflow

**For End Users:**

1. Verify enterprise mode is active:
   ```bash
   copaw skills search "" --limit 1
   ```
   If enterprise mode is active, it will only show enterprise hub skills.

2. Search for skills (audit log is created automatically):
   ```bash
   copaw skills search "automation" --limit 10
   ```

3. Install skill (signature is verified automatically):
   ```bash
   copaw skills install automation --enable
   ```

### Enterprise Installation by Slug

In enterprise mode, you can install skills directly by slug without the full URL:

```bash
# Standard mode requires full URL or uses default
# Enterprise mode uses enterprise hub URL automatically
copaw skills install my-custom-skill --enable

# The CLI automatically:
# - Uses COPAW_SKILLS_HUB_BASE_URL
# - Verifies signature with COPAW_SKILLS_HUB_PUBLIC_KEY
# - Logs to audit with COPAW_EMPLOYEE_ID
```

## AI Integration Examples

### Example 1: Task-Based Skill Discovery

**User Request**: "I need to automate some repetitive tasks."

**AI Response**:
```
Let me search for automation-related skills for you.

[Executes: copaw skills search "automation" --limit 10]

Found 3 skills:
1. automation - Automate repetitive tasks with scripts
2. scheduler - Schedule tasks to run at specific times
3. web-automation - Automate web interactions

Which skill would you like to install?
```

### Example 2: Category-Based Browsing

**User Request**: "What data processing skills are available?"

**AI Response**:
```
Let me search for data processing skills.

[Executes: copaw skills search "data" --limit 20]

Found skills for data processing:
- csv: CSV file manipulation
- json: JSON data processing
- xlsx: Excel file operations
- database: Database query and management

Would you like details on any of these?
```

### Example 3: Multi-Skill Installation

**User Request**: "Set up skills for document processing."

**AI Response**:
```
I'll install the relevant document processing skills.

[Executes: copaw skills install pdf --enable]
[Executes: copaw skills install docx --enable]
[Executes: copaw skills install xlsx --enable]

All document processing skills are now installed and enabled.
```

## Troubleshooting

### Issue: "Enterprise mode is enabled" Error

**Symptom**:
```
ValueError: Enterprise mode is enabled. Access to public ClawHub is prohibited.
```

**Solution**:
1. Check your hub configuration:
   ```bash
   echo $COPAW_SKILLS_HUB_BASE_URL
   echo $COPAW_SKILLS_HUB_PUBLIC_KEY
   ```

2. If enterprise mode is incorrectly enabled, unset the public key:
   ```bash
   unset COPAW_SKILLS_HUB_PUBLIC_KEY
   ```

3. Or set the correct enterprise hub URL:
   ```bash
   export COPAW_SKILLS_HUB_BASE_URL="http://correct-hub:9090"
   ```

### Issue: "Signature verification failed" Error

**Symptom**:
```
ValueError: Enterprise Hub skill signature verification failed.
```

**Solution**:
1. Verify the public key is correct
2. Contact your hub administrator
3. Ensure you're using the official enterprise hub

### Issue: "Skill not found" Error

**Symptom**:
```
RuntimeError: Unable to fetch skill from hub endpoints
```

**Solution**:
1. Verify the skill slug is correct
2. Search for the skill to find the correct slug:
   ```bash
   copaw skills search "skill-name" --limit 20
   ```

3. Check hub connectivity:
   ```bash
   copaw skills search "test" --limit 1
   ```

### Issue: "Skill already exists" Error

**Symptom**:
```
RuntimeError: Failed to create skill 'pdf'. Try overwrite=true if it already exists.
```

**Solution**:
Use the `--force` flag to overwrite:
```bash
copaw skills install pdf --force
```

### Issue: Permission Errors

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: '/path/to/skill'
```

**Solution**:
1. Check write permissions for the skills directory
2. Ensure CoPaw has proper permissions:
   ```bash
   ls -la ~/.copaw/active_skills/
   ```

### Issue: Command Not Found

**Symptom**:
```
bash: copaw: command not found
```

**Solution**:
1. Ensure CoPaw is installed:
   ```bash
   pip install -e ".[full]"
   ```

2. Or use the shell scripts from the active_skills directory:
   ```bash
   ~/.copaw/active_skills/find-skills/scripts/search_skills.sh "pdf" 10
   ```

## Advanced Usage

### Custom Hub URL

To use a custom hub URL temporarily:

```bash
COPAW_SKILLS_HUB_BASE_URL="http://custom-hub:8080" copaw skills search "test" --limit 10
```

### Batch Installation

Install multiple skills at once:

```bash
for skill in pdf docx xlsx; do
    copaw skills install $skill --enable
done
```

### List and Filter

List all skills and filter with grep:

```bash
copaw skills list | grep "pdf"
```

## Best Practices

1. **Use CLI commands directly** when possible - they provide better error handling
2. **Use `--force` carefully** - it overwrites existing skills
3. **Verify enterprise mode** before attempting installations
4. **Search first** to find the correct skill slug before installing
5. **Test skills** after installation to ensure they work correctly
6. **Use `copaw skills list`** to verify installation status

## Comparison: Old vs New Approach

### Old Approach (Python Scripts)

```bash
# Old way - directly importing modules
python scripts/search_skills.py "pdf" 10
python scripts/install_skill.py pdf --enable
```

**Issues:**
- Direct module imports
- Security concerns
- Duplicated logic

### New Approach (CLI Commands)

```bash
# New way - using CoPaw CLI
copaw skills search "pdf" --limit 10
copaw skills install pdf --enable

# Or via shell scripts
./scripts/search_skills.sh "pdf" 10
./scripts/install_skill.sh pdf --enable
```

**Benefits:**
- Standard CLI interface
- Centralized security handling
- Enterprise mode support
- Consistent error handling
- Better maintainability
