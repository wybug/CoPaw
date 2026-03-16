# -*- coding: utf-8 -*-
"""Data models for enterprise skills hub."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SkillBundle:
    """A skill bundle with files and metadata."""

    name: str
    content: str
    files: dict[str, str]
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "content": self.content,
            "files": self.files,
            "version": self.version,
        }


@dataclass
class SkillRecord:
    """A skill record in storage."""

    slug: str
    name: str
    description: str
    version: str
    status: str  # "pending", "approved", "rejected"
    signature: str = ""
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    approver: str = ""


@dataclass
class ApprovalRecord:
    """An approval record for skill submissions."""

    id: str
    skill_slug: str
    submitted_at: datetime
    status: str  # "pending", "approved", "rejected"
    reviewer: str = ""
    reviewed_at: datetime | None = None
    comment: str = ""


@dataclass
class MCPServerRecord:
    """An MCP server record in storage."""

    slug: str
    name: str
    description: str
    version: str
    status: str  # "pending", "approved", "rejected"
    transport: str  # "stdio", "streamable_http", "sse"
    command: str = ""
    args: list[str] | None = None
    url: str = ""
    env_vars: dict[str, str] | None = None
    signature: str = ""
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    approver: str = ""

    def __post_init__(self):
        """Initialize default values for lists and dicts."""
        if self.args is None:
            self.args = []
        if self.env_vars is None:
            self.env_vars = {}
