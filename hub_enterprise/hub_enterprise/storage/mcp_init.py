# -*- coding: utf-8 -*-
"""Pre-populated MCP server configurations for enterprise store."""
from typing import Dict, Any, List


# Common MCP servers that are pre-populated in the enterprise store
PRE_POPULATED_MCP_SERVERS: List[Dict[str, Any]] = [
    {
        "slug": "tavily-search",
        "name": "Tavily Search",
        "description": "Web search using Tavily API for accurate, real-time results. Requires TAVILY_API_KEY environment variable.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-tavily-search"],
        "url": "",
        "env_vars": {
            "TAVILY_API_KEY": "your-tavily-api-key-here",
        },
    },
    {
        "slug": "fetch",
        "name": "Fetch",
        "description": "HTTP fetch tool for making web requests and scraping content. Supports various content types.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
        "url": "",
        "env_vars": {},
    },
    {
        "slug": "filesystem",
        "name": "Filesystem",
        "description": "File system operations for reading, writing, and managing files. Use with caution in production.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str("/path/to/allowed/files")],
        "url": "",
        "env_vars": {},
    },
    {
        "slug": "brave-search",
        "name": "Brave Search",
        "description": "Web search using Brave Search API for privacy-focused search results. Requires BRAVE_API_KEY environment variable.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "url": "",
        "env_vars": {
            "BRAVE_API_KEY": "your-brave-api-key-here",
        },
    },
    {
        "slug": "sequential-thinking",
        "name": "Sequential Thinking",
        "description": "Chain of thought reasoning tool for step-by-step problem solving and analysis.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        "url": "",
        "env_vars": {},
    },
    {
        "slug": "github",
        "name": "GitHub",
        "description": "GitHub integration for managing repositories, issues, and pull requests. Requires GITHUB_TOKEN environment variable.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "url": "",
        "env_vars": {
            "GITHUB_TOKEN": "your-github-token-here",
        },
    },
    {
        "slug": "postgres",
        "name": "PostgreSQL",
        "description": "PostgreSQL database connector for querying and managing databases. Requires DATABASE_URL environment variable.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "url": "",
        "env_vars": {
            "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname",
        },
    },
    {
        "slug": "slack",
        "name": "Slack",
        "description": "Slack integration for sending messages and managing channels. Requires SLACK_TOKEN environment variable.",
        "version": "1.0.0",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "url": "",
        "env_vars": {
            "SLACK_TOKEN": "your-slack-token-here",
        },
    },
]


def get_pre_populated_servers() -> List[Dict[str, Any]]:
    """Get list of pre-populated MCP servers.

    Returns:
        List of MCP server configurations.
    """
    return PRE_POPULATED_MCP_SERVERS


def get_server_by_slug(slug: str) -> Dict[str, Any] | None:
    """Get pre-populated server by slug.

    Args:
        slug: Server slug identifier.

    Returns:
        Server configuration or None if not found.
    """
    for server in PRE_POPULATED_MCP_SERVERS:
        if server["slug"] == slug:
            return server
    return None
