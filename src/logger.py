"""
日志配置模块

提供统一的日志系统，替代 print/console.print 混用。
"""
import logging
import sys
from typing import Optional

from rich.logging import RichHandler
from rich.console import Console

__all__ = ["get_logger", "setup_logging", "logger"]

# 全局 Console 对象（用于 RichHandler）
_console: Optional[Console] = None

# 默认日志器
logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    force: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    设置日志系统

    Args:
        level: 日志级别，默认 INFO
        force: 是否强制重新配置（即使已配置）
        log_file: 日志文件路径（可选），写入文件

    Returns:
        配置好的 logger 对象
    """
    global logger, _console

    # 如果已配置且不强制，直接返回
    if logger is not None and not force:
        return logger

    # 创建 console
    _console = Console(force_terminal=True, force_jupyter=False)

    # 创建 logger
    logger = logging.getLogger("promptpro")
    logger.setLevel(level)

    # 清除已有的 handlers
    logger.handlers.clear()

    # 添加 RichHandler（输出到控制台）
    rich_handler = RichHandler(
        console=_console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
    )
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)

    # 如果指定了日志文件，添加 FileHandler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # 防止日志传播到根 logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取子模块日志器

    Args:
        name: 子模块名称

    Returns:
        子模块 logger 对象
    """
    if logger is None:
        setup_logging()
    return logger.getChild(name)
