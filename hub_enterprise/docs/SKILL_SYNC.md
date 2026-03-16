# Skills Sync Guide

Enterprise CoPaw skills synchronization tool for importing skills from external sources (GitHub, skills.sh, skillsmp.com) into your private Hub with automatic RSA signing and approval.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Reference](#command-reference)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Installation

The skills sync tool is included with the enterprise Hub installation.

### From Source

```bash
cd hub_enterprise
pip install -e .
```

### Verify Installation

```bash
skills-sync --version
# Output: skills-sync, version 1.0.0
```

## Quick Start

### 1. Generate Key Pair

First, generate an RSA key pair for signing skills:

```bash
skills-sync generate-key-pair --output ~/.copaw/keys
```

This creates:
- `~/.copaw/keys/private_key.pem` - Keep this secret!
- `~/.copaw/keys/public_key.pem` - Distribute for verification

### 2. Configure CoPaw

Set the public key in your CoPaw enterprise environment:

```bash
export COPAW_SKILLS_HUB_PUBLIC_KEY="$(cat ~/.copaw/keys/public_key.pem)"
```

### 3. Sync a Skill

```bash
# Sync from GitHub
skills-sync sync github https://github.com/owner/repo --auto-approve \
  --private-key-file ~/.copaw/keys/private_key.pem

# Sync from skills.sh
skills-sync sync skills-sh https://skills.sh/owner/repo/skill-name \
  --auto-approve --private-key-file ~/.copaw/keys/private_key.pem
```

## Configuration

Configuration is loaded from environment variables or command-line options.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HUB_SYNC_URL` | Hub server URL | `http://localhost:9090` |
| `HUB_SYNC_PRIVATE_KEY` | RSA private key (PEM format) | - |
| `HUB_SYNC_PRIVATE_KEY_FILE` | Path to private key file | - |
| `HUB_SYNC_AUTO_APPROVE` | Auto-approve skills | `false` |
| `HUB_SYNC_DRY_RUN` | Preview mode | `false` |
| `HUB_SYNC_LOG_FILE` | Log file path | - |
| `HUB_SYNC_TIMEOUT` | HTTP timeout (seconds) | `30` |
| `HUB_SYNC_RETRIES` | Retry attempts | `3` |
| `HUB_PRIVATE_KEY` | Fallback private key | - |
| `HUB_DATA_DIR` | Hub data directory (direct mode) | - |
| `GITHUB_TOKEN` | GitHub API token (for rate limits) | - |

### Config File (Optional)

Create `~/.copaw/sync_config.yaml`:

```yaml
hub_url: http://localhost:9090
private_key_file: ~/.copaw/keys/private_key.pem
auto_approve: true
dry_run: false
log_file: ~/.copaw/sync.log
timeout: 30
retries: 3
```

## Command Reference

### `skills-sync sync`

Sync a skill from a source to the enterprise Hub.

```bash
skills-sync sync [OPTIONS] SOURCE IDENTIFIER
```

**Arguments:**
- `SOURCE` - Source type: `github`, `skills-sh`, `skills-mp`, `auto`
- `IDENTIFIER` - URL, slug, or owner/repo

**Options:**
| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--hub-url URL` | `HUB_SYNC_URL` | Hub server URL |
| `--private-key PEM` | `HUB_SYNC_PRIVATE_KEY` | RSA private key |
| `--private-key-file PATH` | `HUB_SYNC_PRIVATE_KEY_FILE` | Private key file |
| `--auto-approve` / `--no-auto-approve` | `HUB_SYNC_AUTO_APPROVE` | Auto-approve skills |
| `--dry-run` | `HUB_SYNC_DRY_RUN` | Preview mode |
| `--log-file PATH` | `HUB_SYNC_LOG_FILE` | Log file path |
| `--verbose`, `-v` | - | Debug logging |
| `--quiet`, `-q` | - | Suppress console output |
| `--direct` | - | Use direct storage mode |
| `--data-dir PATH` | `HUB_DATA_DIR` | Hub data directory |

### `skills-sync generate-key-pair`

Generate a new RSA key pair for signing skills.

```bash
skills-sync generate-key-pair [OPTIONS]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o PATH` | Current directory | Output directory |
| `--private-name NAME` | `private_key.pem` | Private key filename |
| `--public-name NAME` | `public_key.pem` | Public key filename |

### `skills-sync verify`

Verify a skill bundle signature.

```bash
skills-sync verify [OPTIONS] BUNDLE_FILE
```

**Options:**
| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--public-key PEM` | `COPAW_SKILLS_HUB_PUBLIC_KEY` | Public key |
| `--public-key-file PATH` | - | Public key file |
| `--signature SIG` | - | Base64 signature |

## Usage Examples

### Basic Sync from GitHub

```bash
# Sync from repository root
skills-sync sync github https://github.com/anthropics/enterprise-skills

# Sync from specific path
skills-sync sync github https://github.com/owner/repo/tree/main/skills/my-skill

# Sync using owner/repo format
skills-sync sync github owner/repo
```

### Sync with Auto-Approval

```bash
skills-sync sync github owner/repo --auto-approve \
  --private-key-file ~/.copaw/keys/private_key.pem
```

### Preview Mode (Dry Run)

```bash
skills-sync sync github owner/repo --dry-run --verbose
```

Output:
```
[DRY RUN] Would fetch from: owner/repo
[DRY RUN] Skill details:
  Name: My Skill
  Slug: my-skill
  Description: An awesome skill
  Files: 5
  Source: https://github.com/owner/repo
  [Would auto-approve with signature]
```

### Sync from skills.sh

```bash
skills-sync sync skills-sh https://skills.sh/anthropics/enterprise-skills/analyzer \
  --auto-approve --private-key-file ~/.copaw/keys/private_key.pem
```

### Direct Storage Mode

Bypass HTTP API and write directly to Hub storage:

```bash
skills-sync sync github owner/repo --direct \
  --data-dir /path/to/hub/skills_data \
  --auto-approve --private-key-file ~/.copaw/keys/private_key.pem
```

### Batch Sync with Environment Configuration

```bash
# Set up environment
export HUB_SYNC_URL=http://hub.example.com:9090
export HUB_SYNC_PRIVATE_KEY_FILE=~/.copaw/keys/private_key.pem
export HUB_SYNC_AUTO_APPROVE=true

# Sync multiple skills
skills-sync sync github owner/skill1
skills-sync sync github owner/skill2
skills-sync sync skills-sh https://skills.sh/owner/repo/skill3
```

### Verify a Signed Skill

```bash
skills-sync verify skill_bundle.json \
  --public-key-file ~/.copaw/keys/public_key.pem
```

## Troubleshooting

### Private Key Errors

**Error:** `Private key is required when auto_approve is enabled`

**Solution:** Ensure the private key is provided:
```bash
export HUB_SYNC_PRIVATE_KEY_FILE=~/.copaw/keys/private_key.pem
# Or
export HUB_SYNC_PRIVATE_KEY="$(cat ~/.copaw/keys/private_key.pem)"
```

### Hub Connection Errors

**Error:** `Failed to submit skill: Connection refused`

**Solution:** Check that the Hub is running:
```bash
# Check Hub status
curl http://localhost:9090/api/v1/search

# Start Hub if needed
cd hub_enterprise
python -m hub_enterprise
```

### GitHub Rate Limiting

**Error:** `GitHub API rate limit exceeded`

**Solution:** Set a GitHub token:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Signature Verification Failures

**Error:** `Enterprise Hub skill signature verification failed`

**Solutions:**
1. Ensure public/private key pair match
2. Check that bundle wasn't modified after signing
3. Verify key format (PEM, PKCS8)

### Direct Mode Permission Errors

**Error:** `Permission denied` when using `--direct`

**Solution:** Ensure proper permissions on data directory:
```bash
chmod 755 /path/to/hub/skills_data
```

### Logging Issues

Enable verbose logging for debugging:
```bash
skills-sync sync github owner/repo --verbose --log-file sync_debug.log
```

## Security Best Practices

1. **Never commit private keys** to version control
2. **Use environment variables** for production deployments
3. **Restrict key file permissions**: `chmod 600 private_key.pem`
4. **Rotate keys periodically** for enhanced security
5. **Verify signatures** after sync operations
6. **Use separate keys** for development and production

## Advanced Usage

### Custom Slug Generation

The sync tool automatically generates slugs from skill names. To customize:

1. Fork the sync script
2. Modify the `_sync_single_skill` function
3. Update the slug generation logic

### Custom Storage Backend

To use a custom storage backend:

1. Extend `HubSubmitter` class
2. Override submission methods
3. Pass custom submitter to sync function

### Integration with CI/CD

```yaml
# .github/workflows/sync-skills.yml
name: Sync Skills to Hub
on:
  push:
    paths:
      - 'skills/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -e hub_enterprise/
      - name: Sync skills
        env:
          HUB_SYNC_URL: ${{ secrets.HUB_URL }}
          HUB_SYNC_PRIVATE_KEY: ${{ secrets.HUB_PRIVATE_KEY }}
          HUB_SYNC_AUTO_APPROVE: "true"
        run: |
          skills-sync sync github ${{ github.repository }}
```

## Support

For issues and questions:
- Check logs: `--log-file sync.log --verbose`
- Verify Hub status: `curl http://localhost:9090/api/v1/search`
- Review configuration: `skills-sync sync github owner/repo --dry-run`
