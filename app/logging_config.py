"""Centralized logging configuration."""

import logging
import os


def setup_logging() -> None:
    """Configure stdlib logging with a structured format.

    Level is controlled by the LOG_LEVEL environment variable (default: INFO).
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    )
