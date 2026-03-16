"""
自定义异常模块

提供分层的异常体系，用于更精确地错误处理。
"""
from typing import Optional, Any


class ErrorCode:
    """错误码常量"""

    # 配置错误 (1xx)
    CONFIG_LOAD_FAILED = 101
    CONFIG_SAVE_FAILED = 102
    CONFIG_INVALID = 103
    CONFIG_PARSE_ERROR = 104

    # 连接错误 (2xx)
    CONNECTION_FAILED = 201
    CONNECTION_TIMEOUT = 202
    CONNECTION_REFUSED = 203

    # 模型错误 (3xx)
    MODEL_NOT_FOUND = 301
    MODEL_LOAD_FAILED = 302
    MODEL_UNAVAILABLE = 303

    # 优化错误 (4xx)
    OPTIMIZER_FAILED = 401
    OPTIMIZER_TIMEOUT = 402
    OPTIMIZER_INVALID_INPUT = 403

    # 历史记录错误 (5xx)
    HISTORY_LOAD_FAILED = 501
    HISTORY_SAVE_FAILED = 502

    # 剪贴板错误 (6xx)
    CLIPBOARD_COPY_FAILED = 601

    # 需求文档错误 (7xx)
    REQUIREMENT_NOT_FOUND = 701
    REQUIREMENT_INVALID = 702
    REQUIREMENT_READ_FAILED = 703

    # 通用错误 (9xx)
    UNKNOWN_ERROR = 999


class PromptProError(Exception):
    """所有 PromptPro 自定义异常的基类"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"[{self.error_code}] {self.message} - 详情: {self.details}"
        return f"[{self.error_code}] {self.message}"


class ConfigError(PromptProError):
    """配置相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CONFIG_LOAD_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ConnectionError(PromptProError):
    """与 LLM 服务连接相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CONNECTION_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ModelError(PromptProError):
    """模型相关错误（如模型不存在、加载失败）"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.MODEL_NOT_FOUND,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class OptimizerError(PromptProError):
    """Prompt 优化过程中的错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.OPTIMIZER_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class TemplateError(PromptProError):
    """模板相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class HistoryError(PromptProError):
    """历史记录相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.HISTORY_LOAD_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ClipboardError(PromptProError):
    """剪贴板相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CLIPBOARD_COPY_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class RequirementError(PromptProError):
    """需求文档相关错误"""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.REQUIREMENT_NOT_FOUND,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)