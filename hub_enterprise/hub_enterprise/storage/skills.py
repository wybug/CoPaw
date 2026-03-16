# -*- coding: utf-8 -*-
"""Skills storage module."""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..models import SkillBundle, SkillRecord


class SkillStorage:
    """Storage for skills."""

    def __init__(self, db_path: str | None = None, data_dir: str | None = None):
        """Initialize skill storage.

        Args:
            db_path: Path to SQLite database.
            data_dir: Path to skills data directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "skills_data" / "skills.db"
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
                CREATE TABLE IF NOT EXISTS skills (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
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
        bundle: SkillBundle,
    ) -> str:
        """Create a pending skill submission.

        Args:
            slug: Skill slug.
            name: Skill name.
            description: Skill description.
            version: Skill version.
            bundle: Skill bundle data.

        Returns:
            The skill slug.
        """
        submitted_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO skills
                (slug, name, description, version, status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (slug, name, description, version, "pending", submitted_at.isoformat()),
            )
            conn.commit()

        # Save bundle to pending directory
        pending_dir = self.data_dir / "pending" / slug
        pending_dir.mkdir(parents=True, exist_ok=True)
        self._save_bundle(pending_dir, bundle)

        return slug

    def approve_skill(
        self,
        slug: str,
        signature: str,
        approver: str = "",
    ) -> bool:
        """Approve a skill and move it to approved directory.

        Args:
            slug: Skill slug.
            signature: Signature for the skill.
            approver: Approver name or ID.

        Returns:
            True if successful.
        """
        approved_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE skills
                SET status = ?, signature = ?, approved_at = ?, approver = ?
                WHERE slug = ?
                """,
                ("approved", signature, approved_at.isoformat(), approver, slug),
            )
            conn.commit()

            if cursor.rowcount == 0:
                return False

        # Move bundle from pending to approved
        pending_dir = self.data_dir / "pending" / slug
        approved_dir = self.data_dir / "approved" / slug
        approved_dir.mkdir(parents=True, exist_ok=True)

        if pending_dir.exists():
            import shutil
            if approved_dir.exists():
                shutil.rmtree(approved_dir)
            shutil.copytree(pending_dir, approved_dir)

        return True

    def reject_skill(
        self,
        slug: str,
        reason: str = "",
    ) -> bool:
        """Reject a skill submission.

        Args:
            slug: Skill slug.
            reason: Rejection reason.

        Returns:
            True if successful.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE skills
                SET status = ?
                WHERE slug = ?
                """,
                ("rejected", slug),
            )
            conn.commit()

            if cursor.rowcount == 0:
                return False

        return True

    def get_by_slug(self, slug: str) -> Optional[SkillRecord]:
        """Get a skill by slug.

        Args:
            slug: Skill slug.

        Returns:
            Skill record or None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT slug, name, description, version, status, signature,
                       submitted_at, approved_at, approver
                FROM skills WHERE slug = ?
                """,
                (slug,),
            )
            row = cursor.fetchone()

            if row:
                return SkillRecord(
                    slug=row[0],
                    name=row[1],
                    description=row[2],
                    version=row[3],
                    status=row[4],
                    signature=row[5] or "",
                    submitted_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    approved_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    approver=row[8] or "",
                )
        return None

    def get_bundle(self, skill: SkillRecord) -> SkillBundle:
        """Get skill bundle from storage.

        Args:
            skill: Skill record.

        Returns:
            Skill bundle.
        """
        if skill.status == "approved":
            bundle_dir = self.data_dir / "approved" / skill.slug
        else:
            bundle_dir = self.data_dir / "pending" / skill.slug

        return self._load_bundle(bundle_dir, skill.name)

    def search(
        self,
        query: str = "",
        status: str = "approved",
        limit: int = 20,
    ) -> list[SkillRecord]:
        """Search skills.

        Args:
            query: Search query string.
            status: Filter by status.
            limit: Maximum results.

        Returns:
            List of skill records.
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
                SELECT slug, name, description, version, status, signature,
                       submitted_at, approved_at, approver
                FROM skills
                WHERE {' AND '.join(conditions)}
                ORDER BY approved_at DESC
                LIMIT ?
                """,
                params,
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    SkillRecord(
                        slug=row[0],
                        name=row[1],
                        description=row[2],
                        version=row[3],
                        status=row[4],
                        signature=row[5] or "",
                        submitted_at=datetime.fromisoformat(row[6]) if row[6] else None,
                        approved_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        approver=row[8] or "",
                    )
                )
            return results

    def _save_bundle(self, directory: Path, bundle: SkillBundle) -> None:
        """Save skill bundle to directory.

        Args:
            directory: Target directory.
            bundle: Skill bundle to save.
        """
        # Save SKILL.md
        with open(directory / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(bundle.content)

        # Save files
        for path, content in bundle.files.items():
            file_path = directory / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    def _load_bundle(self, directory: Path, name: str) -> SkillBundle:
        """Load skill bundle from directory.

        Args:
            directory: Source directory.
            name: Skill name.

        Returns:
            Skill bundle.
        """
        # Helper to remove BOM if present
        def _remove_bom(text: str) -> str:
            if text.startswith('\ufeff'):
                return text[1:]
            return text

        # Load SKILL.md
        skill_md = directory / "SKILL.md"
        content = ""
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            content = _remove_bom(content)

        # Load files
        files: dict[str, str] = {}
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.name != "SKILL.md":
                    rel_path = str(file_path.relative_to(directory))
                    file_content = file_path.read_text(encoding="utf-8")
                    files[rel_path] = _remove_bom(file_content)

        return SkillBundle(name=name, content=content, files=files)
