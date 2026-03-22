"""Shared logging utilities for PromptPro."""

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

__all__ = ["get_logger", "setup_logging", "logger"]

_console: Optional[Console] = None
logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    force: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure the root PromptPro logger."""
    global _console, logger

    if logger is not None and not force:
        return logger

    _console = Console(force_terminal=True, force_jupyter=False)

    configured_logger = logging.getLogger("promptpro")
    configured_logger.setLevel(level)
    configured_logger.handlers.clear()

    rich_handler = RichHandler(
        console=_console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
    )
    rich_handler.setLevel(level)
    configured_logger.addHandler(rich_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        configured_logger.addHandler(file_handler)

    configured_logger.propagate = False
    logger = configured_logger
    return configured_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the shared PromptPro logger."""
    global logger
    if logger is None:
        setup_logging()
    assert logger is not None
    return logger.getChild(name)
