"""Tests for project-specific exceptions."""

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


class TestErrorCodes:
    def test_error_codes_exist(self):
        assert ErrorCode.CONFIG_LOAD_FAILED == 101
        assert ErrorCode.CONNECTION_FAILED == 201
        assert ErrorCode.MODEL_NOT_FOUND == 301
        assert ErrorCode.OPTIMIZER_FAILED == 401
        assert ErrorCode.UNKNOWN_ERROR == 999


class TestPromptProError:
    def test_basic_error(self):
        error = PromptProError("Test error")
        assert str(error) == "[999] Test error"
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.UNKNOWN_ERROR

    def test_error_with_code(self):
        error = PromptProError("Test error", error_code=ErrorCode.CONFIG_LOAD_FAILED)
        assert error.error_code == ErrorCode.CONFIG_LOAD_FAILED
        assert "[101]" in str(error)

    def test_error_with_details(self):
        error = PromptProError("Test error", details="extra context")
        assert "extra context" in str(error)
        assert "Details" in str(error)


class TestSpecificErrors:
    def test_config_error(self):
        error = ConfigError("Config load failed")
        assert error.error_code == ErrorCode.CONFIG_LOAD_FAILED

    def test_connection_error(self):
        error = ConnectionError("Connection failed")
        assert error.error_code == ErrorCode.CONNECTION_FAILED

    def test_model_error(self):
        error = ModelError("Model not found")
        assert error.error_code == ErrorCode.MODEL_NOT_FOUND

    def test_optimizer_error(self):
        error = OptimizerError("Optimization failed")
        assert error.error_code == ErrorCode.OPTIMIZER_FAILED

    def test_history_error(self):
        error = HistoryError("History load failed")
        assert error.error_code == ErrorCode.HISTORY_LOAD_FAILED

    def test_clipboard_error(self):
        error = ClipboardError("Clipboard copy failed")
        assert error.error_code == ErrorCode.CLIPBOARD_COPY_FAILED
