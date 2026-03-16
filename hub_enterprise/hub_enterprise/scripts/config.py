# -*- coding: utf-8 -*-
"""Configuration management for skills sync script.

This module handles configuration loading from environment variables
and optional config files for the skills sync script.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SyncConfig:
    """Configuration for skills sync operations.

    Attributes:
        hub_url: URL of the enterprise Hub server.
        private_key: RSA private key in PEM format for signing skills.
        private_key_file: Path to file containing private key.
        auto_approve: Whether to automatically approve skills after submission.
        dry_run: If True, preview operations without executing them.
        log_file: Optional path to log file for output.
        timeout: HTTP timeout in seconds for API requests.
        retries: Number of retry attempts for failed requests.
    """

    hub_url: str = "http://localhost:9090"
    private_key: Optional[str] = None
    private_key_file: Optional[str] = None
    auto_approve: bool = False
    dry_run: bool = False
    log_file: Optional[str] = None
    timeout: int = 30
    retries: int = 3

    def __post_init__(self):
        """Load private key from file if specified."""
        # Load private key from file if key not directly provided
        if not self.private_key and self.private_key_file:
            key_path = Path(self.private_key_file)
            if key_path.exists():
                self.private_key = key_path.read_text(encoding="utf-8")
            else:
                raise ValueError(f"Private key file not found: {self.private_key_file}")

        # Validate private key is available if auto-approve is enabled
        if self.auto_approve and not self.private_key:
            raise ValueError(
                "Private key is required when auto_approve is enabled. "
                "Set HUB_SYNC_PRIVATE_KEY or HUB_SYNC_PRIVATE_KEY_FILE."
            )


def load_config(
    hub_url: str | None = None,
    private_key: str | None = None,
    private_key_file: str | None = None,
    auto_approve: bool | None = None,
    dry_run: bool | None = None,
    log_file: str | None = None,
    timeout: int | None = None,
    retries: int | None = None,
) -> SyncConfig:
    """Load configuration from parameters and environment variables.

    Priority (highest to lowest):
    1. Function parameters
    2. Environment variables (HUB_SYNC_*)
    3. Default values

    Environment Variables:
        HUB_SYNC_URL: Hub server URL (default: http://localhost:9090)
        HUB_SYNC_PRIVATE_KEY: RSA private key in PEM format
        HUB_SYNC_PRIVATE_KEY_FILE: Path to file containing private key
        HUB_SYNC_AUTO_APPROVE: Auto-approve skills ("true" or "false")
        HUB_SYNC_DRY_RUN: Preview mode without changes ("true" or "false")
        HUB_SYNC_LOG_FILE: Path to log file
        HUB_SYNC_TIMEOUT: HTTP timeout in seconds (default: 30)
        HUB_SYNC_RETRIES: Number of retries (default: 3)
        HUB_PRIVATE_KEY: Fallback private key (used if HUB_SYNC_PRIVATE_KEY not set)

    Args:
        hub_url: Override Hub URL.
        private_key: Override private key directly.
        private_key_file: Override private key file path.
        auto_approve: Override auto-approve setting.
        dry_run: Override dry-run setting.
        log_file: Override log file path.
        timeout: Override timeout value.
        retries: Override retries value.

    Returns:
        SyncConfig instance with loaded configuration.
    """
    # Helper to parse boolean from string
    def parse_bool(value: str | None, default: bool = False) -> bool:
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    # Helper to parse int from string
    def parse_int(value: str | None, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    # Load Hub URL
    config_hub_url = hub_url or os.environ.get(
        "HUB_SYNC_URL", "http://localhost:9090"
    )

    # Load private key (try multiple sources)
    config_private_key = private_key or os.environ.get(
        "HUB_SYNC_PRIVATE_KEY"
    ) or os.environ.get("HUB_PRIVATE_KEY")

    # Load private key file
    config_private_key_file = private_key_file or os.environ.get(
        "HUB_SYNC_PRIVATE_KEY_FILE"
    )

    # Load auto-approve setting
    config_auto_approve = auto_approve if auto_approve is not None else parse_bool(
        os.environ.get("HUB_SYNC_AUTO_APPROVE", "false")
    )

    # Load dry-run setting
    config_dry_run = dry_run if dry_run is not None else parse_bool(
        os.environ.get("HUB_SYNC_DRY_RUN", "false")
    )

    # Load log file
    config_log_file = log_file or os.environ.get("HUB_SYNC_LOG_FILE")

    # Load timeout
    config_timeout = timeout if timeout is not None else parse_int(
        os.environ.get("HUB_SYNC_TIMEOUT"), 30
    )

    # Load retries
    config_retries = retries if retries is not None else parse_int(
        os.environ.get("HUB_SYNC_RETRIES"), 3
    )

    return SyncConfig(
        hub_url=config_hub_url,
        private_key=config_private_key,
        private_key_file=config_private_key_file,
        auto_approve=config_auto_approve,
        dry_run=config_dry_run,
        log_file=config_log_file,
        timeout=config_timeout,
        retries=config_retries,
    )


def get_default_config_path() -> Path:
    """Get the default configuration file path.

    Returns:
        Path to default config file (~/.copaw/sync_config.yaml).
    """
    home = Path.home()
    return home / ".copaw" / "sync_config.yaml"


def load_config_from_file(path: str | None = None) -> dict:
    """Load configuration from YAML file.

    Args:
        path: Path to config file. If None, uses default path.

    Returns:
        Dictionary with configuration values.

    Raises:
        ImportError: If pyyaml is not installed.
        FileNotFoundError: If config file doesn't exist.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "pyyaml is required to load config from file. "
            "Install with: pip install pyyaml"
        )

    config_path = Path(path) if path else get_default_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
