# -*- coding: utf-8 -*-
"""MCP management API (compatible with CoPaw mcp_hub.py)."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ..storage.mcp import MCPStorage


class SubmitMCPRequest(BaseModel):
    """Request model for submitting an MCP server."""

    slug: str
    name: str
    description: str
    transport: str = "stdio"  # "stdio", "streamable_http", "sse"
    command: str = ""
    args: List[str] = []
    url: str = ""
    env_vars: Dict[str, str] = {}
    version: str = "1.0.0"


router = APIRouter(prefix="/api/v1", tags=["mcp"])
storage = MCPStorage()


@router.get("/mcp/search")
async def search_mcp_servers(
    q: str = Query(""),
    limit: int = Query(20),
) -> Dict[str, Any]:
    """Search approved MCP servers (compatible with CoPaw search_hub_mcp_servers).

    CoPaw calls: search_hub_mcp_servers(query, limit)
    Environment: COPAW_MCP_HUB_BASE_URL + COPAW_MCP_HUB_SEARCH_PATH
    """
    results = storage.search(query=q, status="approved", limit=limit)

    # Compatible with CoPaw's search format
    return {
        "items": [
            {
                "slug": s.slug,
                "name": s.name,
                "displayName": s.name,
                "description": s.description,
                "summary": s.description,
                "version": s.version,
                "transport": s.transport,
                "url": f"/mcp/{s.slug}",
            }
            for s in results
        ]
    }


@router.get("/mcp/servers/{slug}")
async def get_mcp_server(slug: str) -> Dict[str, Any]:
    """Get MCP server details (compatible with CoPaw install_mcp_server_from_hub).

    CoPaw calls: install_mcp_server_from_hub(slug, enable)
    Environment: COPAW_MCP_HUB_BASE_URL + COPAW_MCP_HUB_DETAIL_PATH
    """
    server = storage.get_by_slug(slug)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    if server.status != "approved":
        raise HTTPException(status_code=403, detail="MCP server not approved")

    # Compatible with CoPaw's MCP server spec format
    return {
        "slug": server.slug,
        "name": server.name,
        "displayName": server.name,
        "description": server.description,
        "version": server.version,
        "transport": server.transport,
        "command": server.command,
        "args": server.args,
        "url": server.url,
        "env_vars": server.env_vars,
        "signature": server.signature,
    }


@router.post("/mcp/servers/submit")
async def submit_mcp_server(request: SubmitMCPRequest) -> Dict[str, Any]:
    """Submit a new MCP server for approval (internal API)."""
    # Check if slug already exists
    existing = storage.get_by_slug(request.slug)
    if existing and existing.status == "approved":
        raise HTTPException(status_code=409, detail="MCP server already exists")

    # Create pending MCP server
    storage.create_pending(
        request.slug,
        request.name,
        request.description,
        request.version,
        request.transport,
        request.command,
        request.args,
        request.url,
        request.env_vars,
    )

    return {
        "slug": request.slug,
        "status": "pending",
    }
