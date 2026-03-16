# CoPaw Enterprise Mode

CoPaw supports an enterprise mode that provides a private skills registry with signature verification and audit logging.

## Overview

Enterprise mode enables:
- **Private Skills Registry**: Host your own skills registry instead of using public ClawHub
- **Signature Verification**: All skills are cryptographically signed before installation
- **Approval Workflow**: Skills require approval before being available for installation
- **Audit Logging**: Track all skill operations (search, install, enable, disable)

## Configuration

### Server Side (Enterprise Hub)

Set up the enterprise backend server:

```bash
cd hub_enterprise

# Generate key pair
python -c "from hub_enterprise.signature import generate_key_pair; private, public = generate_key_pair(); print('Private:'); print(private); print('\nPublic:'); print(public)"

# Set environment variables
export HUB_HOST=0.0.0.0
export HUB_PORT=9090
export HUB_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."

# Start server
python -m hub_enterprise
```

### Client Side (CoPaw)

Configure CoPaw to use the enterprise hub:

```bash
# Point to enterprise hub
export COPAW_SKILLS_HUB_BASE_URL="http://your-server:9090"

# Add public key for signature verification
export COPAW_SKILLS_HUB_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"

# Employee ID for audit logging
export COPAW_EMPLOYEE_ID="EMP001"
```

## Environment Variables

### Enterprise Hub Server

| Variable | Description | Default |
|----------|-------------|---------|
| `HUB_HOST` | Server host | `0.0.0.0` |
| `HUB_PORT` | Server port | `9090` |
| `HUB_PRIVATE_KEY` | RSA private key for signing (PEM format) | - |
| `HUB_DATA_DIR` | Data directory path | `./skills_data` |
| `HUB_RELOAD` | Auto-reload on code changes | `false` |
| `HUB_LOG_LEVEL` | Logging level | `info` |

### CoPaw Client

| Variable | Description | Default |
|----------|-------------|---------|
| `COPAW_SKILLS_HUB_BASE_URL` | Hub server URL | `https://clawhub.ai` |
| `COPAW_SKILLS_HUB_PUBLIC_KEY` | Public key for verification (PEM format) | - |
| `COPAW_EMPLOYEE_ID` | Employee ID for audit logs | `unknown` |

## Installation

```bash
# Install CoPaw with enterprise dependencies
pip install -e ".[enterprise]"

# Or install cryptography separately
pip install cryptography>=41.0.0
```

## Security Policy

### Enterprise Mode (Public Key Configured)

When `COPAW_SKILLS_HUB_PUBLIC_KEY` is set:

1. **Prohibited Public Hub Access**: Access to public ClawHub is blocked
2. **Mandatory Signature Verification**: All skills must be signed
3. **Approval Process**: Skills must be approved before installation
4. **Audit Trail**: All operations are logged with employee IDs

### Standard Mode (No Public Key)

Without `COPAW_SKILLS_HUB_PUBLIC_KEY`:

1. Uses public ClawHub (`https://clawhub.ai`)
2. No signature verification
3. No audit logging
4. Existing behavior preserved

## API Endpoints

### Skills (CoPaw Compatible)

- `GET /api/v1/search?q=query&limit=20` - Search approved skills
- `GET /api/v1/skills/{slug}` - Get skill details with signature
- `GET /api/v1/skills/{slug}/file?path=...` - Get skill file
- `POST /api/v1/skills/submit` - Submit skill for approval

### Approvals

- `GET /api/v1/approvals/pending` - List pending approvals
- `GET /api/v1/approvals/{approval_id}` - Get approval details
- `POST /api/v1/approvals/{approval_id}/approve` - Approve skill (generates signature)
- `POST /api/v1/approvals/{approval_id}/reject` - Reject skill

### Audit Logs

- `POST /api/v1/audit/logs` - Create audit log
- `GET /api/v1/audit/logs` - Query audit logs
- `GET /api/v1/audit/logs/{log_id}` - Get audit log details

## Workflow

### Submitting a Skill

1. Submit skill to enterprise hub for approval
2. Admin reviews the skill
3. If approved, server signs the skill with private key
4. Skill becomes available for installation

### Installing a Skill

1. CoPaw requests skill from enterprise hub
2. Hub returns skill with signature
3. CoPaw verifies signature using public key
4. If valid, skill is installed
5. Audit log is sent to hub

## Audit Log Actions

The following actions are logged:

- `search_skill` - Skill search operations
- `install_skill` - Skill installation (success/failed)
- `enable_skill` - Skill enablement (success/failed)
- `disable_skill` - Skill disablement (success/failed)

Each log entry includes:
- Employee ID
- Timestamp
- Action type
- Resource name
- Details (JSON object)
- Status (success/failed)
