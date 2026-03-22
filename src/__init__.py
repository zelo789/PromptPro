"""PromptPro package exports."""

__version__ = "0.4.0"
__author__ = "PromptPro Team"

from src.config import Config, global_config
from src.exceptions import (
    ClipboardError,
    ConfigError,
    ConnectionError,
    ErrorCode,
    HistoryError,
    ModelError,
    OptimizerError,
    PromptProError,
)
from src.history import HistoryManager, global_history
from src.ollama_client import LLMClient, OllamaClient
from src.optimizer import PromptOptimizer

__all__ = [
    "Config",
    "global_config",
    "LLMClient",
    "OllamaClient",
    "PromptOptimizer",
    "HistoryManager",
    "global_history",
    "PromptProError",
    "ConfigError",
    "ConnectionError",
    "ModelError",
    "OptimizerError",
    "HistoryError",
    "ClipboardError",
    "ErrorCode",
]
