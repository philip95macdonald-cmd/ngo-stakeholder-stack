"""
Einfaches strukturiertes Logging fuer alle Tools.
Loglevel kommt aus LOG_LEVEL Env-Var (Default INFO).
"""

from __future__ import annotations

import logging
import os
import sys


def setup(level: str = "INFO") -> None:
    """Root-Logger konfigurieren. Wird einmal pro Prozess aufgerufen."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger
