"""
PromptPro - 让 Prompt 更懂 AI

主要功能：
- 多 LLM 提供商支持（Ollama、OpenAI、Claude、自定义 API）
- 7 种 Prompt 框架（CO-STAR, RTF, CREATE, APE, BROKE, RISEN, TAG）
- 智能框架推荐
- 多版本对比
- 历史记录
- 剪贴板支持
"""

__version__ = "0.4.0"
__author__ = "PromptPro Team"

from src.config import Config, global_config, get_config
from src.ollama_client import LLMClient, OllamaClient
from src.optimizer import PromptOptimizer
from src.history import HistoryManager, global_history, get_history_manager
from src.exceptions import (
    PromptProError,
    ConfigError,
    ConnectionError,
    ModelError,
    OptimizerError,
    HistoryError,
    ClipboardError,
    ErrorCode,
)

__all__ = [
    "Config",
    "global_config",
    "get_config",
    "LLMClient",
    "OllamaClient",  # 向后兼容别名
    "PromptOptimizer",
    "HistoryManager",
    "global_history",
    "get_history_manager",
    "PromptProError",
    "ConfigError",
    "ConnectionError",
    "ModelError",
    "OptimizerError",
    "HistoryError",
    "ClipboardError",
    "ErrorCode",
]
