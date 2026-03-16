# -*- coding: utf-8 -*-
"""Initialize MCP store with pre-populated servers.

This script is run on hub startup to ensure common MCP servers are available.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to import hub_enterprise modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hub_enterprise.storage.mcp import MCPStorage
from hub_enterprise.storage.mcp_init import get_pre_populated_servers

logger = logging.getLogger(__name__)


def init_mcp_servers(signature: str = "", approver: str = "system") -> int:
    """Initialize MCP store with pre-populated servers.

    Args:
        signature: Enterprise signature for auto-approved servers.
        approver: Approver name for audit log.

    Returns:
        Number of servers initialized.
    """
    storage = MCPStorage()
    servers = get_pre_populated_servers()
    initialized = 0

    for server_config in servers:
        slug = server_config["slug"]

        # Check if server already exists
        existing = storage.get_by_slug(slug)
        if existing:
            logger.info(f"MCP server '{slug}' already exists, skipping")
            continue

        # Create pending server
        storage.create_pending(
            slug=slug,
            name=server_config["name"],
            description=server_config["description"],
            version=server_config["version"],
            transport=server_config["transport"],
            command=server_config.get("command", ""),
            args=server_config.get("args", []),
            url=server_config.get("url", ""),
            env_vars=server_config.get("env_vars", {}),
        )

        # Auto-approve with enterprise signature
        storage.approve_server(
            slug=slug,
            signature=signature,
            approver=approver,
        )

        logger.info(f"Initialized MCP server '{slug}'")
        initialized += 1

    return initialized


def main() -> None:
    """Main entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # For enterprise mode, you would use the actual private key to sign
    # For now, use a placeholder signature
    signature = "ENTERPRISE_SIGNED"

    count = init_mcp_servers(signature=signature)
    print(f"Initialized {count} MCP servers")

    if count > 0:
        print("\nInitialized servers:")
        for server in get_pre_populated_servers():
            print(f"  - {server['slug']}: {server['name']}")


if __name__ == "__main__":
    main()
