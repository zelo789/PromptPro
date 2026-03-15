"""
剪贴板工具模块

提供跨平台的剪贴板复制功能。
"""
import sys
from typing import Optional

from src.exceptions import ClipboardError, ErrorCode
from src.logger import get_logger

logger = get_logger("clipboard")


def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到剪贴板

    Args:
        text: 要复制的文本

    Returns:
        bool: 是否成功

    Raises:
        ClipboardError: 复制失败时抛出
    """
    if not text:
        logger.warning("尝试复制空文本到剪贴板")
        return False

    # 尝试使用 pyperclip
    try:
        import pyperclip
        pyperclip.copy(text)
        logger.debug(f"已复制 {len(text)} 个字符到剪贴板")
        return True
    except ImportError:
        logger.debug("pyperclip 未安装，尝试使用系统命令")
    except Exception as e:
        logger.warning(f"pyperclip 复制失败：{e}")

    # 尝试使用系统命令
    return _copy_with_system_command(text)


def _copy_with_system_command(text: str) -> bool:
    """使用系统命令复制到剪贴板"""
    import subprocess

    try:
        if sys.platform == "win32":
            # Windows: 使用 clip 命令
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                shell=True,
            )
            process.communicate(text.encode("utf-8"))
            logger.debug("已通过 clip 命令复制到剪贴板")
            return True

        elif sys.platform == "darwin":
            # macOS: 使用 pbcopy 命令
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
            )
            process.communicate(text.encode("utf-8"))
            logger.debug("已通过 pbcopy 命令复制到剪贴板")
            return True

        elif sys.platform.startswith("linux"):
            # Linux: 尝试 xclip 或 xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                    )
                    process.communicate(text.encode("utf-8"))
                    logger.debug(f"已通过 {cmd[0]} 命令复制到剪贴板")
                    return True
                except FileNotFoundError:
                    continue

            logger.warning("Linux 系统未找到 xclip 或 xsel")
            return False

        else:
            logger.warning(f"不支持的系统平台：{sys.platform}")
            return False

    except Exception as e:
        logger.error(f"系统命令复制失败：{e}")
        raise ClipboardError(
            "复制到剪贴板失败",
            error_code=ErrorCode.CLIPBOARD_COPY_FAILED,
            details=str(e),
        )


def get_from_clipboard() -> Optional[str]:
    """
    从剪贴板获取文本

    Returns:
        Optional[str]: 剪贴板中的文本，失败返回 None
    """
    try:
        import pyperclip
        text = pyperclip.paste()
        logger.debug(f"从剪贴板获取了 {len(text)} 个字符")
        return text
    except ImportError:
        logger.debug("pyperclip 未安装，无法从剪贴板读取")
        return None
    except Exception as e:
        logger.warning(f"从剪贴板读取失败：{e}")
        return None


def is_clipboard_available() -> bool:
    """
    检查剪贴板功能是否可用

    Returns:
        bool: 是否可用
    """
    # 检查 pyperclip
    try:
        import pyperclip
        return True
    except ImportError:
        pass

    # 检查系统命令
    import shutil

    if sys.platform == "win32":
        return shutil.which("clip") is not None
    elif sys.platform == "darwin":
        return shutil.which("pbcopy") is not None
    elif sys.platform.startswith("linux"):
        return shutil.which("xclip") is not None or shutil.which("xsel") is not None

    return False