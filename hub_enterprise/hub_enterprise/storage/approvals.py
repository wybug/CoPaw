# -*- coding: utf-8 -*-
"""Approvals storage module."""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..models import ApprovalRecord, SkillBundle


class ApprovalStorage:
    """Storage for approval records."""

    def __init__(self, db_path: str | None = None, data_dir: str | None = None):
        """Initialize approval storage.

        Args:
            db_path: Path to SQLite database.
            data_dir: Path to approvals data directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "skills_data" / "approvals.db"
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "skills_data"

        self.db_path = Path(db_path)
        self.data_dir = Path(data_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    skill_slug TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reviewer TEXT,
                    reviewed_at TEXT,
                    comment TEXT
                )
            """)
            conn.commit()

    def create(
        self,
        skill_slug: str,
        bundle: SkillBundle,
        submitter: str = "",
    ) -> str:
        """Create a new approval request.

        Args:
            skill_slug: Skill slug.
            bundle: Skill bundle data.
            submitter: Submitter name or ID.

        Returns:
            Approval ID.
        """
        approval_id = str(uuid.uuid4())
        submitted_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO approvals
                (id, skill_slug, submitted_at, status)
                VALUES (?, ?, ?, ?)
                """,
                (approval_id, skill_slug, submitted_at.isoformat(), "pending"),
            )
            conn.commit()

        # Save bundle data
        bundle_path = self.data_dir / "approvals" / f"{approval_id}.json"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(bundle.to_dict(), f, ensure_ascii=False, indent=2)

        return approval_id

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        """Get an approval record.

        Args:
            approval_id: Approval ID.

        Returns:
            Approval record or None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, skill_slug, submitted_at, status, reviewer, reviewed_at, comment
                FROM approvals WHERE id = ?
                """,
                (approval_id,),
            )
            row = cursor.fetchone()

            if row:
                return ApprovalRecord(
                    id=row[0],
                    skill_slug=row[1],
                    submitted_at=datetime.fromisoformat(row[2]),
                    status=row[3],
                    reviewer=row[4] or "",
                    reviewed_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    comment=row[6] or "",
                )
        return None

    def get_skill_data(self, approval_id: str) -> dict[str, Any]:
        """Get skill bundle data for an approval.

        Args:
            approval_id: Approval ID.

        Returns:
            Skill bundle data dictionary.
        """
        bundle_path = self.data_dir / "approvals" / f"{approval_id}.json"
        if bundle_path.exists():
            with open(bundle_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def list_pending(self) -> list[ApprovalRecord]:
        """List pending approvals.

        Returns:
            List of pending approval records.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, skill_slug, submitted_at, status, reviewer, reviewed_at, comment
                FROM approvals
                WHERE status = 'pending'
                ORDER BY submitted_at DESC
                """,
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    ApprovalRecord(
                        id=row[0],
                        skill_slug=row[1],
                        submitted_at=datetime.fromisoformat(row[2]),
                        status=row[3],
                        reviewer=row[4] or "",
                        reviewed_at=datetime.fromisoformat(row[5]) if row[5] else None,
                        comment=row[6] or "",
                    )
                )
            return results

    def update_status(
        self,
        approval_id: str,
        status: str,
        reviewer: str = "",
        comment: str = "",
    ) -> bool:
        """Update approval status.

        Args:
            approval_id: Approval ID.
            status: New status ("approved" or "rejected").
            reviewer: Reviewer name or ID.
            comment: Review comment.

        Returns:
            True if successful.
        """
        reviewed_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE approvals
                SET status = ?, reviewer = ?, reviewed_at = ?, comment = ?
                WHERE id = ?
                """,
                (status, reviewer, reviewed_at.isoformat(), comment, approval_id),
            )
            conn.commit()

            return cursor.rowcount > 0

    def delete(self, approval_id: str) -> bool:
        """Delete an approval record.

        Args:
            approval_id: Approval ID.

        Returns:
            True if successful.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM approvals WHERE id = ?",
                (approval_id,),
            )
            conn.commit()

            # Delete bundle data
            bundle_path = self.data_dir / "approvals" / f"{approval_id}.json"
            if bundle_path.exists():
                bundle_path.unlink()

            return cursor.rowcount > 0
