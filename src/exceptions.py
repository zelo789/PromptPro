"""Project-specific exception hierarchy for PromptPro."""

from typing import Any, Optional


class ErrorCode:
    """Stable error codes used across the project."""

    CONFIG_LOAD_FAILED = 101
    CONFIG_SAVE_FAILED = 102
    CONFIG_INVALID = 103
    CONFIG_PARSE_ERROR = 104

    CONNECTION_FAILED = 201
    CONNECTION_TIMEOUT = 202
    CONNECTION_REFUSED = 203

    MODEL_NOT_FOUND = 301
    MODEL_LOAD_FAILED = 302
    MODEL_UNAVAILABLE = 303

    OPTIMIZER_FAILED = 401
    OPTIMIZER_TIMEOUT = 402
    OPTIMIZER_INVALID_INPUT = 403

    HISTORY_LOAD_FAILED = 501
    HISTORY_SAVE_FAILED = 502

    CLIPBOARD_COPY_FAILED = 601

    REQUIREMENT_NOT_FOUND = 701
    REQUIREMENT_INVALID = 702
    REQUIREMENT_READ_FAILED = 703

    UNKNOWN_ERROR = 999


class PromptProError(Exception):
    """Base class for all PromptPro-specific exceptions."""

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
        if self.details is not None:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


class ConfigError(PromptProError):
    """Raised for configuration loading, parsing, or validation failures."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CONFIG_LOAD_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ConnectionError(PromptProError):
    """Raised for network and provider connectivity failures."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CONNECTION_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ModelError(PromptProError):
    """Raised for missing or unusable model selections."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.MODEL_NOT_FOUND,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class OptimizerError(PromptProError):
    """Raised when prompt analysis or optimization fails."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.OPTIMIZER_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class TemplateError(PromptProError):
    """Raised for template-related failures."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class HistoryError(PromptProError):
    """Raised for history storage and retrieval failures."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.HISTORY_LOAD_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class ClipboardError(PromptProError):
    """Raised when clipboard integration fails."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.CLIPBOARD_COPY_FAILED,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)


class RequirementError(PromptProError):
    """Raised for requirement document parsing and loading failures."""

    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.REQUIREMENT_NOT_FOUND,
        details: Optional[Any] = None,
    ):
        super().__init__(message, error_code, details)
