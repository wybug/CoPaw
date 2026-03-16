# -*- coding: utf-8 -*-
"""Audit log storage module."""
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List


@dataclass
class AuditLog:
    """An audit log entry."""

    id: str
    employee_id: str
    action: str
    resource_type: str
    resource_name: str
    details: dict[str, Any]
    status: str
    timestamp: datetime


class AuditStorage:
    """Storage for audit logs."""

    def __init__(self, db_path: str | None = None):
        """Initialize audit storage.

        Args:
            db_path: Path to SQLite database.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "skills_data" / "audit.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_name TEXT NOT NULL,
                    details TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_employee_id
                ON audit_logs(employee_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_action
                ON audit_logs(action)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource_name
                ON audit_logs(resource_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON audit_logs(timestamp DESC)
            """)
            conn.commit()

    def create_log(
        self,
        employee_id: str,
        action: str,
        resource_type: str,
        resource_name: str,
        details: dict[str, Any],
        status: str,
        timestamp: datetime,
    ) -> str:
        """Create an audit log entry.

        Args:
            employee_id: Employee ID.
            action: Action performed.
            resource_type: Type of resource.
            resource_name: Name of resource.
            details: Additional details.
            status: Status of action.
            timestamp: Timestamp of action.

        Returns:
            Log ID.
        """
        log_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_logs
                (id, employee_id, action, resource_type, resource_name, details, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    employee_id,
                    action,
                    resource_type,
                    resource_name,
                    json.dumps(details),
                    status,
                    timestamp.isoformat(),
                ),
            )
            conn.commit()
        return log_id

    def list_logs(
        self,
        employee_id: str | None = None,
        action: str | None = None,
        resource_name: str | None = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Query audit logs.

        Args:
            employee_id: Filter by employee ID.
            action: Filter by action.
            resource_name: Filter by resource name.
            limit: Maximum results.

        Returns:
            List of audit log entries.
        """
        conditions = []
        params = []

        if employee_id:
            conditions.append("employee_id = ?")
            params.append(employee_id)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if resource_name:
            conditions.append("resource_name = ?")
            params.append(resource_name)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT id, employee_id, action, resource_type, resource_name, details, status, timestamp
                FROM audit_logs
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params,
            )

            logs = []
            for row in cursor.fetchall():
                logs.append(
                    AuditLog(
                        id=row[0],
                        employee_id=row[1],
                        action=row[2],
                        resource_type=row[3],
                        resource_name=row[4],
                        details=json.loads(row[5]),
                        status=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                    )
                )
            return logs

    def get_log(self, log_id: str) -> Optional[AuditLog]:
        """Get a single audit log entry.

        Args:
            log_id: Log ID.

        Returns:
            Audit log entry or None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, employee_id, action, resource_type, resource_name, details, status, timestamp
                FROM audit_logs
                WHERE id = ?
                """,
                (log_id,),
            )

            row = cursor.fetchone()
            if row:
                return AuditLog(
                    id=row[0],
                    employee_id=row[1],
                    action=row[2],
                    resource_type=row[3],
                    resource_name=row[4],
                    details=json.loads(row[5]),
                    status=row[6],
                    timestamp=datetime.fromisoformat(row[7]),
                )
            return None
