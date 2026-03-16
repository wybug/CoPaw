# -*- coding: utf-8 -*-
"""MCP storage module."""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict

from ..models import MCPServerRecord


class MCPStorage:
    """Storage for MCP servers."""

    def __init__(self, db_path: str | None = None, data_dir: str | None = None):
        """Initialize MCP storage.

        Args:
            db_path: Path to SQLite database.
            data_dir: Path to MCP data directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "mcp_data" / "mcp.db"
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "mcp_data"

        self.db_path = Path(db_path)
        self.data_dir = Path(data_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    command TEXT,
                    args TEXT,
                    url TEXT,
                    env_vars TEXT,
                    signature TEXT,
                    submitted_at TEXT,
                    approved_at TEXT,
                    approver TEXT
                )
            """)
            conn.commit()

    def create_pending(
        self,
        slug: str,
        name: str,
        description: str,
        version: str,
        transport: str,
        command: str = "",
        args: List[str] | None = None,
        url: str = "",
        env_vars: Dict[str, str] | None = None,
    ) -> str:
        """Create a pending MCP server submission.

        Args:
            slug: MCP server slug.
            name: MCP server name.
            description: MCP server description.
            version: MCP server version.
            transport: Transport type (stdio, streamable_http, sse).
            command: Command to launch the server.
            args: Command arguments.
            url: URL for HTTP/SSE transports.
            env_vars: Environment variables.

        Returns:
            The MCP server slug.
        """
        submitted_at = datetime.utcnow()
        args_json = json.dumps(args or [])
        env_vars_json = json.dumps(env_vars or {})

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO mcp_servers
                (slug, name, description, version, status, transport, command, args, url, env_vars, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slug, name, description, version, "pending", transport,
                    command, args_json, url, env_vars_json, submitted_at.isoformat(),
                ),
            )
            conn.commit()

        return slug

    def approve_server(
        self,
        slug: str,
        signature: str,
        approver: str = "",
    ) -> bool:
        """Approve an MCP server.

        Args:
            slug: MCP server slug.
            signature: Signature for the server.
            approver: Approver name or ID.

        Returns:
            True if successful.
        """
        approved_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE mcp_servers
                SET status = ?, signature = ?, approved_at = ?, approver = ?
                WHERE slug = ?
                """,
                ("approved", signature, approved_at.isoformat(), approver, slug),
            )
            conn.commit()

            if cursor.rowcount == 0:
                return False

        return True

    def reject_server(
        self,
        slug: str,
        reason: str = "",
    ) -> bool:
        """Reject an MCP server submission.

        Args:
            slug: MCP server slug.
            reason: Rejection reason.

        Returns:
            True if successful.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE mcp_servers
                SET status = ?
                WHERE slug = ?
                """,
                ("rejected", slug),
            )
            conn.commit()

            if cursor.rowcount == 0:
                return False

        return True

    def get_by_slug(self, slug: str) -> Optional[MCPServerRecord]:
        """Get an MCP server by slug.

        Args:
            slug: MCP server slug.

        Returns:
            MCP server record or None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT slug, name, description, version, status, transport,
                       command, args, url, env_vars, signature,
                       submitted_at, approved_at, approver
                FROM mcp_servers WHERE slug = ?
                """,
                (slug,),
            )
            row = cursor.fetchone()

            if row:
                args = json.loads(row[7]) if row[7] else []
                env_vars = json.loads(row[9]) if row[9] else {}
                return MCPServerRecord(
                    slug=row[0],
                    name=row[1],
                    description=row[2],
                    version=row[3],
                    status=row[4],
                    transport=row[5],
                    command=row[6] or "",
                    args=args,
                    url=row[8] or "",
                    env_vars=env_vars,
                    signature=row[10] or "",
                    submitted_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    approved_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    approver=row[13] or "",
                )
        return None

    def search(
        self,
        query: str = "",
        status: str = "approved",
        limit: int = 20,
    ) -> List[MCPServerRecord]:
        """Search MCP servers.

        Args:
            query: Search query string.
            status: Filter by status.
            limit: Maximum results.

        Returns:
            List of MCP server records.
        """
        conditions = ["status = ?"]
        params = [status]

        if query:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT slug, name, description, version, status, transport,
                       command, args, url, env_vars, signature,
                       submitted_at, approved_at, approver
                FROM mcp_servers
                WHERE {' AND '.join(conditions)}
                ORDER BY approved_at DESC
                LIMIT ?
                """,
                params,
            )

            results = []
            for row in cursor.fetchall():
                args = json.loads(row[7]) if row[7] else []
                env_vars = json.loads(row[9]) if row[9] else {}
                results.append(
                    MCPServerRecord(
                        slug=row[0],
                        name=row[1],
                        description=row[2],
                        version=row[3],
                        status=row[4],
                        transport=row[5],
                        command=row[6] or "",
                        args=args,
                        url=row[8] or "",
                        env_vars=env_vars,
                        signature=row[10] or "",
                        submitted_at=datetime.fromisoformat(row[11]) if row[11] else None,
                        approved_at=datetime.fromisoformat(row[12]) if row[12] else None,
                        approver=row[13] or "",
                    )
                )
            return results
