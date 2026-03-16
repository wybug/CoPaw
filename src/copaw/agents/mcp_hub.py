# -*- coding: utf-8 -*-
"""MCP hub client and install helpers."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


@dataclass
class HubMCPServerResult:
    """Result from searching MCP servers on the hub."""
    slug: str
    name: str
    description: str = ""
    version: str = ""
    transport: str = "stdio"
    source_url: str = ""


@dataclass
class HubMCPInstallResult:
    """Result from installing an MCP server from the hub."""
    name: str
    enabled: bool
    slug: str


RETRYABLE_HTTP_STATUS = {
    408,
    409,
    425,
    429,
    500,
    502,
    503,
    504,
}


def _mcp_hub_http_timeout() -> float:
    """Get HTTP timeout for MCP hub requests."""
    raw = os.environ.get("COPAW_MCP_HUB_HTTP_TIMEOUT", "15")
    try:
        return max(3.0, float(raw))
    except Exception:
        return 15.0


def _mcp_hub_http_retries() -> int:
    """Get HTTP retry count for MCP hub requests."""
    raw = os.environ.get("COPAW_MCP_HUB_HTTP_RETRIES", "3")
    try:
        return max(0, int(raw))
    except Exception:
        return 3


def _compute_backoff_seconds(attempt: int) -> float:
    """Compute exponential backoff delay."""
    base = 0.8
    cap = 6.0
    return min(cap, base * (2 ** max(0, attempt - 1)))


def get_mcp_hub_base_url() -> str:
    """Get MCP hub base URL from environment variable."""
    return os.environ.get("COPAW_MCP_HUB_BASE_URL", "https://clawhub.ai")


def _mcp_hub_search_path() -> str:
    """Get MCP hub search path from environment variable."""
    return os.environ.get(
        "COPAW_MCP_HUB_SEARCH_PATH",
        "/api/v1/mcp/search",
    )


def _mcp_hub_detail_path() -> str:
    """Get MCP hub detail path from environment variable."""
    return os.environ.get(
        "COPAW_MCP_HUB_DETAIL_PATH",
        "/api/v1/mcp/servers/{slug}",
    )


def _join_url(base: str, path: str) -> str:
    """Join base URL and path."""
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _http_get(
    url: str,
    params: dict[str, Any] | None = None,
    accept: str = "application/json",
) -> str:
    """Make HTTP GET request with retries."""
    full_url = url
    if params:
        full_url = f"{url}?{urlencode(params)}"
    req = Request(
        full_url,
        headers={
            "Accept": accept,
            "User-Agent": "copaw-mcp-hub/1.0",
        },
    )

    retries = _mcp_hub_http_retries()
    timeout = _mcp_hub_http_timeout()
    attempts = retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            last_error = e
            status = getattr(e, "code", 0) or 0
            # Retry only temporary/rate-limit server failures
            if attempt < attempts and status in RETRYABLE_HTTP_STATUS:
                delay = _compute_backoff_seconds(attempt)
                logger.warning(
                    "MCP Hub HTTP %s on %s (attempt %d/%d), retrying in %.2fs",
                    status,
                    full_url,
                    attempt,
                    attempts,
                    delay,
                )
                import time
                time.sleep(delay)
                continue
            raise
        except URLError as e:
            last_error = e
            if attempt < attempts:
                delay = _compute_backoff_seconds(attempt)
                logger.warning(
                    "MCP Hub URL error on %s (attempt %d/%d), retrying in %.2fs: %s",
                    full_url,
                    attempt,
                    attempts,
                    delay,
                    e,
                )
                import time
                time.sleep(delay)
                continue
            raise
        except TimeoutError as e:
            last_error = e
            if attempt < attempts:
                delay = _compute_backoff_seconds(attempt)
                logger.warning(
                    "MCP Hub timeout on %s (attempt %d/%d), retrying in %.2fs",
                    full_url,
                    attempt,
                    attempts,
                    delay,
                )
                import time
                time.sleep(delay)
                continue
            raise

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to request MCP hub URL: {full_url}")


def _http_json_get(url: str, params: dict[str, Any] | None = None) -> Any:
    """Make HTTP GET request and parse JSON response."""
    body = _http_get(url, params=params, accept="application/json")
    return json.loads(body)


def _norm_search_items(data: Any) -> list[dict[str, Any]]:
    """Normalize search results from different response formats."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "servers", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        if all(k in data for k in ("name", "slug")):
            return [data]
    return []


def search_hub_mcp_servers(
    query: str = "",
    limit: int = 20,
) -> list[HubMCPServerResult]:
    """Search for MCP servers on the enterprise hub.

    Args:
        query: Search query string.
        limit: Maximum number of results.

    Returns:
        List of MCP server search results.
    """
    base = get_mcp_hub_base_url()
    search_url = _join_url(base, _mcp_hub_search_path())
    data = _http_json_get(search_url, {"q": query, "limit": limit})
    items = _norm_search_items(data)

    results: list[HubMCPServerResult] = []
    for item in items:
        slug = str(item.get("slug") or item.get("name") or "").strip()
        if not slug:
            continue
        results.append(
            HubMCPServerResult(
                slug=slug,
                name=str(
                    item.get("name") or item.get("displayName") or slug,
                ),
                description=str(
                    item.get("description") or item.get("summary") or "",
                ),
                version=str(item.get("version") or ""),
                transport=str(item.get("transport") or "stdio"),
                source_url=str(item.get("url") or ""),
            ),
        )

    return results


def get_hub_mcp_server(slug: str) -> dict[str, Any] | None:
    """Get MCP server details from the hub.

    Args:
        slug: MCP server slug.

    Returns:
        MCP server specification or None if not found.
    """
    base = get_mcp_hub_base_url()
    detail_path = _mcp_hub_detail_path().format(slug=slug)
    detail_url = _join_url(base, detail_path)

    try:
        return _http_json_get(detail_url)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise
    except URLError:
        return None
