# -*- coding: utf-8 -*-
"""Logging utilities for skills sync script.

This module provides structured logging for sync operations,
including both console and file output.
"""
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        success: Whether the operation succeeded.
        skill_name: Name of the skill.
        source: Source URL/identifier.
        message: Success or error message.
        approval_id: Approval ID if submitted for approval.
        signature: Signature if auto-approved.
    """

    success: bool
    skill_name: str
    source: str
    message: str
    approval_id: Optional[str] = None
    signature: Optional[str] = None
    error: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the result."""
        if self.success:
            parts = [f"✓ {self.skill_name}"]
            if self.approval_id:
                parts.append(f"(approval: {self.approval_id[:8]}...)")
            if self.signature:
                parts.append("[auto-approved]")
            return " ".join(parts)
        else:
            return f"✗ {self.skill_name}: {self.error or self.message}"


class SyncLogger:
    """Logger for skills sync operations.

    Provides both console and file logging with formatted output.
    """

    def __init__(
        self,
        name: str = "skills_sync",
        level: int = logging.INFO,
        log_file: Optional[str | Path] = None,
        quiet: bool = False,
    ):
        """Initialize the sync logger.

        Args:
            name: Logger name.
            level: Logging level (default: INFO).
            log_file: Optional path to log file.
            quiet: If True, suppress console output.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        self.quiet = quiet
        self._results: list[SyncResult] = []

        # Console handler
        if not quiet:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console.setFormatter(formatter)
            self.logger.addHandler(console)

        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str, *args) -> None:
        """Log info message."""
        self.logger.info(message, *args)

    def debug(self, message: str, *args) -> None:
        """Log debug message."""
        self.logger.debug(message, *args)

    def warning(self, message: str, *args) -> None:
        """Log warning message."""
        self.logger.warning(message, *args)

    def error(self, message: str, *args) -> None:
        """Log error message."""
        self.logger.error(message, *args)

    def result(self, result: SyncResult) -> None:
        """Log a sync result.

        Args:
            result: SyncResult to log.
        """
        self._results.append(result)
        if result.success:
            self.info(str(result))
        else:
            self.error(str(result))

    def get_results(self) -> list[SyncResult]:
        """Get all logged results.

        Returns:
            List of SyncResult objects.
        """
        return self._results.copy()

    def summary(self) -> str:
        """Generate summary of all logged operations.

        Returns:
            Summary string with success/failure counts.
        """
        total = len(self._results)
        if total == 0:
            return "No operations performed."

        successful = sum(1 for r in self._results if r.success)
        failed = total - successful

        parts = [f"Total: {total}"]
        if successful > 0:
            parts.append(f"Success: {successful}")
        if failed > 0:
            parts.append(f"Failed: {failed}")

        return " | ".join(parts)

    def print_summary(self) -> None:
        """Print summary to console."""
        if not self.quiet:
            print(f"\n{self.summary()}")


def get_logger(
    name: str = "skills_sync",
    log_file: Optional[str] = None,
    quiet: bool = False,
    verbose: bool = False,
) -> SyncLogger:
    """Get a configured sync logger.

    Args:
        name: Logger name.
        log_file: Optional path to log file.
        quiet: If True, suppress console output.
        verbose: If True, enable debug logging.

    Returns:
        Configured SyncLogger instance.
    """
    level = logging.DEBUG if verbose else logging.INFO
    return SyncLogger(name=name, level=level, log_file=log_file, quiet=quiet)
