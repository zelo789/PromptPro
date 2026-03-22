"""Cross-platform clipboard helpers."""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Optional

from src.exceptions import ClipboardError, ErrorCode
from src.logger import get_logger

logger = get_logger("clipboard")


def copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard if possible."""
    if not text:
        logger.warning("Attempted to copy empty text to the clipboard.")
        return False

    try:
        import pyperclip

        pyperclip.copy(text)
        logger.debug("Copied %s characters to the clipboard via pyperclip.", len(text))
        return True
    except ImportError:
        logger.debug("pyperclip is not installed; falling back to system commands.")
    except Exception as exc:
        logger.warning("pyperclip clipboard copy failed: %s", exc)

    return _copy_with_system_command(text)


def _copy_with_system_command(text: str) -> bool:
    """Copy text using a platform-native clipboard command."""
    try:
        if sys.platform == "win32":
            process = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0

        if sys.platform == "darwin":
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0

        if sys.platform.startswith("linux"):
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    process.communicate(text.encode("utf-8"))
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            logger.warning("Clipboard helpers xclip/xsel are not available on this Linux system.")
            return False

        logger.warning("Clipboard copy is not supported on platform %s.", sys.platform)
        return False
    except Exception as exc:
        logger.error("System clipboard copy failed: %s", exc)
        raise ClipboardError(
            "Failed to copy text to the clipboard.",
            error_code=ErrorCode.CLIPBOARD_COPY_FAILED,
            details=str(exc),
        ) from exc


def get_from_clipboard() -> Optional[str]:
    """Read text from the clipboard when pyperclip is available."""
    try:
        import pyperclip

        text = pyperclip.paste()
        logger.debug("Read %s characters from the clipboard.", len(text))
        return text
    except ImportError:
        logger.debug("pyperclip is not installed; clipboard read is unavailable.")
        return None
    except Exception as exc:
        logger.warning("Clipboard read failed: %s", exc)
        return None


def is_clipboard_available() -> bool:
    """Return whether clipboard access is available on this machine."""
    try:
        import pyperclip  # noqa: F401

        return True
    except ImportError:
        pass

    if sys.platform == "win32":
        return shutil.which("clip") is not None
    if sys.platform == "darwin":
        return shutil.which("pbcopy") is not None
    if sys.platform.startswith("linux"):
        return shutil.which("xclip") is not None or shutil.which("xsel") is not None
    return False
