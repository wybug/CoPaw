# CoPaw Enterprise Skills Hub

A private skills registry for CoPaw with signature verification and approval workflow.

## Features

- **Private Skills Registry**: Host your own skills registry instead of using public ClawHub
- **Signature Verification**: All skills are cryptographically signed before installation
- **Approval Workflow**: Skills require approval before being available for installation
- **Audit Logging**: Track all skill operations (search, install, enable, disable)
- **CoPaw Compatible**: Drop-in replacement for public ClawHub

## Installation

```bash
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
# Server Configuration
export HUB_HOST=0.0.0.0
export HUB_PORT=9090

# Private Key (generate with the command below)
export HUB_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
```

### Generate Key Pair

```python
from hub_enterprise.signature import generate_key_pair
private, public = generate_key_pair()
print("Private Key:")
print(private)
print("\nPublic Key:")
print(public)
```

Distribute the **public key** to all CoPaw clients. Keep the **private key** secure on the server.

## Running

```bash
# Direct
python -m hub_enterprise

# Using the CLI
hub-enterprise
```

The server will start on http://localhost:9090

## API Endpoints

### Skills (CoPaw Compatible)

- `GET /api/v1/search?q=query&limit=20` - Search approved skills
- `GET /api/v1/skills/{slug}` - Get skill details
- `GET /api/v1/skills/{slug}/file?path=...` - Get skill file
- `POST /api/v1/skills/submit` - Submit skill for approval

### Approvals

- `GET /api/v1/approvals/pending` - List pending approvals
- `GET /api/v1/approvals/{approval_id}` - Get approval details
- `POST /api/v1/approvals/{approval_id}/approve` - Approve skill
- `POST /api/v1/approvals/{approval_id}/reject` - Reject skill

### Audit Logs

- `POST /api/v1/audit/logs` - Create audit log
- `GET /api/v1/audit/logs` - Query audit logs
- `GET /api/v1/audit/logs/{log_id}` - Get audit log details

## CoPaw Client Configuration

Configure CoPaw to use the enterprise hub:

```bash
# Point to enterprise hub
export COPAW_SKILLS_HUB_BASE_URL="http://your-server:9090"

# Add public key for signature verification
export COPAW_SKILLS_HUB_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----"

# Employee ID for audit logging
export COPAW_EMPLOYEE_ID="EMP001"
```

## Security

- **Private Key**: Never share or commit the private key
- **Public Key**: Distribute to CoPaw clients via secure channels
- **Approval Process**: All skills must be approved before installation
- **Audit Trail**: All operations are logged with employee IDs

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black hub_enterprise

# Type check
mypy hub_enterprise
```
