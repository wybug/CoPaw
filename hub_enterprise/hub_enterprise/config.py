# -*- coding: utf-8 -*-
"""Configuration management for enterprise skills hub."""
import os
from pathlib import Path


def get_private_key() -> str | None:
    """Get the private key from environment variable.

    Returns:
        Private key in PEM format, or None if not configured.
    """
    return os.environ.get("HUB_PRIVATE_KEY")


def get_data_dir() -> Path:
    """Get the data directory path.

    Returns:
        Path to the data directory.
    """
    path = os.environ.get("HUB_DATA_DIR")
    if path:
        return Path(path)
    return Path(__file__).parent.parent / "skills_data"


def get_host() -> str:
    """Get the server host.

    Returns:
        Host address.
    """
    return os.environ.get("HUB_HOST", "0.0.0.0")


def get_port() -> int:
    """Get the server port.

    Returns:
        Port number.
    """
    port = os.environ.get("HUB_PORT", "9090")
    try:
        return int(port)
    except ValueError:
        return 9090


def get_reload() -> bool:
    """Get the auto-reload setting.

    Returns:
        True if auto-reload is enabled.
    """
    return os.environ.get("HUB_RELOAD", "false").lower() == "true"


def get_log_level() -> str:
    """Get the log level.

    Returns:
        Log level (debug, info, warning, error).
    """
    return os.environ.get("HUB_LOG_LEVEL", "info").lower()
