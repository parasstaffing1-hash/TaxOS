"""Logging infrastructure setup.

Bridges structlog with the standard library logging module
for consistent structured logging throughout the application.
"""

from __future__ import annotations

from taxos.core.config import Settings
from taxos.core.logging import setup_logging


def configure_logging(settings: Settings) -> None:
    """Configure application logging based on settings."""
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
    )
