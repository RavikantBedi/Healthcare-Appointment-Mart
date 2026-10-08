"""
Structured logging configuration.

Provides consistent log formatting across all modules.
Uses Python's built-in logging — no external dependencies.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger with a structured format.

    Args:
        level: Logging level (default: INFO).
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Args:
        name: Logger name — typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
